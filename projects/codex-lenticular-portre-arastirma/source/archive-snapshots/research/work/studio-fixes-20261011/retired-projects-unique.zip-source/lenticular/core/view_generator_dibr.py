"""Depth-Image Based Rendering (DIBR) for multi-view generation.

Generates multiple view images from a single source photo and
disparity map using forward warping with z-buffer compositing.
Designed for fast preview; Blender pipeline handles final quality.
"""

import logging
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def generate_views_dibr(source_image: np.ndarray,
                        disparity_map: np.ndarray,
                        n_views: int,
                        fill_holes: bool = True,
                        hole_fill_method: str = "interpolate") -> List[np.ndarray]:
    """Generate multi-view images using DIBR forward warping.
    
    For each view k:
      s_k = k/(N-1) - 0.5
      x_shifted = x + s_k × disparity(x, y)
    
    Uses z-buffer to resolve occlusions (foreground pixels overwrite
    background when multiple source pixels map to same target).
    
    Args:
        source_image: Source photograph (H, W, 3) uint8
        disparity_map: Total disparity map in pixels (float32)
                       Positive = foreground, negative = background
        n_views: Number of views to generate
        fill_holes: Whether to fill disocclusion holes
        hole_fill_method: 'interpolate' (fast) or 'push_pull' (better quality)
        
    Returns:
        List of N view images, each (H, W, 3) uint8
    """
    H, W = source_image.shape[:2]
    views = []
    
    for k in range(n_views):
        s_k = k / (n_views - 1) - 0.5 if n_views > 1 else 0.0
        
        # Forward warp
        warped, hole_mask = _forward_warp(
            source_image, disparity_map, s_k
        )
        
        # Fill holes
        if fill_holes and hole_mask.any():
            if hole_fill_method == "push_pull":
                warped = _push_pull_fill(warped, hole_mask)
            else:
                warped = _interpolate_fill(warped, hole_mask)
        
        views.append(warped)
        logger.debug(f"View {k+1}/{n_views}: s_k={s_k:.3f}, "
                     f"holes={hole_mask.sum()/(H*W)*100:.1f}%")
    
    logger.info(f"Generated {n_views} DIBR views")
    return views


def _forward_warp(source: np.ndarray, disparity: np.ndarray,
                  scale: float) -> Tuple[np.ndarray, np.ndarray]:
    """Forward warp source image using scaled disparity.
    
    Args:
        source: Source image (H, W, 3)
        disparity: Disparity map (H, W)
        scale: View interpolation scale (-0.5 to +0.5)
        
    Returns:
        (warped_image, hole_mask) tuple
    """
    H, W = source.shape[:2]
    warped = np.zeros_like(source)
    zbuffer = np.full((H, W), -np.inf, dtype=np.float32)
    hole_mask = np.ones((H, W), dtype=bool)
    
    # Compute target x coordinates
    shift = scale * disparity
    x_coords = np.arange(W, dtype=np.float32)
    
    # Process row by row (vectorized within rows)
    for y in range(H):
        x_target = x_coords + shift[y]
        x_target_int = np.round(x_target).astype(np.int32)
        depths = disparity[y]  # Use disparity as depth proxy
        
        # Valid target positions
        valid = (x_target_int >= 0) & (x_target_int < W)
        
        # Sort by depth (background first, so foreground overwrites)
        valid_indices = np.where(valid)[0]
        if len(valid_indices) == 0:
            continue
        
        # Sort by depth ascending (far to near)
        depth_order = np.argsort(depths[valid_indices])
        sorted_indices = valid_indices[depth_order]
        
        for x_src in sorted_indices:
            x_dst = x_target_int[x_src]
            d = depths[x_src]
            
            if d >= zbuffer[y, x_dst]:
                zbuffer[y, x_dst] = d
                warped[y, x_dst] = source[y, x_src]
                hole_mask[y, x_dst] = False
    
    return warped, hole_mask


def _interpolate_fill(image: np.ndarray, 
                      hole_mask: np.ndarray) -> np.ndarray:
    """Fill holes using horizontal interpolation.
    
    Fast but simple: extends nearest non-hole pixel horizontally.
    """
    result = image.copy()
    H, W = image.shape[:2]
    
    for y in range(H):
        row_mask = hole_mask[y]
        if not row_mask.any():
            continue
        if row_mask.all():
            continue
        
        # Find hole regions and fill from left/right neighbors
        non_hole_indices = np.where(~row_mask)[0]
        hole_indices = np.where(row_mask)[0]
        
        if len(non_hole_indices) == 0:
            continue
        
        # For each hole pixel, find nearest non-hole pixel
        for x_hole in hole_indices:
            # Find nearest non-hole index
            dists = np.abs(non_hole_indices - x_hole)
            nearest_idx = non_hole_indices[np.argmin(dists)]
            result[y, x_hole] = image[y, nearest_idx]
    
    return result


def _push_pull_fill(image: np.ndarray, 
                    hole_mask: np.ndarray) -> np.ndarray:
    """Fill holes using push-pull pyramid interpolation.
    
    Better quality than simple interpolation. Builds a pyramid
    of averaged values and pulls from coarser levels for holes.
    """
    result = image.copy().astype(np.float32)
    weight = (~hole_mask).astype(np.float32)
    
    # Build push pyramid (downsample)
    push_levels = [(result.copy(), weight.copy())]
    current_img = result.copy()
    current_weight = weight.copy()
    
    max_levels = int(np.log2(min(image.shape[:2]))) - 1
    
    for level in range(max_levels):
        h, w = current_img.shape[:2]
        if h < 4 or w < 4:
            break
        
        # Weighted downsample
        new_h, new_w = h // 2, w // 2
        weighted_img = current_img * current_weight[:, :, np.newaxis]
        
        down_weighted_img = cv2.resize(weighted_img, (new_w, new_h),
                                        interpolation=cv2.INTER_AREA)
        down_weight = cv2.resize(current_weight, (new_w, new_h),
                                  interpolation=cv2.INTER_AREA)
        
        # Avoid division by zero
        safe_weight = np.maximum(down_weight, 1e-6)
        down_img = down_weighted_img / safe_weight[:, :, np.newaxis]
        
        push_levels.append((down_img, down_weight))
        current_img = down_img
        current_weight = down_weight
    
    # Pull: upsample from coarse to fine, filling holes
    for level in range(len(push_levels) - 2, -1, -1):
        target_img, target_weight = push_levels[level]
        h, w = target_img.shape[:2]
        
        if level < len(push_levels) - 1:
            coarse_img, _ = push_levels[level + 1]
            upsampled = cv2.resize(coarse_img, (w, h),
                                    interpolation=cv2.INTER_LINEAR)
            
            # Fill only where weight is low
            mask = target_weight < 0.5
            target_img[mask] = upsampled[mask]
            target_weight[mask] = 0.5
        
        push_levels[level] = (target_img, target_weight)
    
    result = push_levels[0][0]
    return np.clip(result, 0, 255).astype(np.uint8)


def generate_views_layered(layers: List[dict],
                           disparity_maps: List[np.ndarray],
                           n_views: int,
                           output_size: Tuple[int, int] = None) -> List[np.ndarray]:
    """Generate multi-view from separated layers.
    
    Each layer is warped independently and composited back-to-front.
    This avoids stretching artifacts at layer boundaries.
    
    Args:
        layers: List of dicts with 'image' (RGBA) and 'depth_order' (0=back)
        disparity_maps: List of disparity maps, one per layer
        n_views: Number of views
        output_size: (H, W) output size (uses first layer if None)
        
    Returns:
        List of N composited view images (H, W, 3)
    """
    if output_size is None:
        output_size = layers[0]['image'].shape[:2]
    
    H, W = output_size
    views = []
    
    # Sort layers back to front
    sorted_layers = sorted(zip(layers, disparity_maps),
                           key=lambda x: x[0]['depth_order'])
    
    for k in range(n_views):
        s_k = k / (n_views - 1) - 0.5 if n_views > 1 else 0.0
        
        # Start with transparent background
        composite = np.zeros((H, W, 4), dtype=np.uint8)
        
        for layer, disp in sorted_layers:
            img = layer['image']  # RGBA
            
            # Warp this layer
            warped_rgba, _ = _forward_warp_rgba(img, disp, s_k)
            
            # Alpha composite (over operation)
            composite = _alpha_composite(composite, warped_rgba)
        
        views.append(composite[:, :, :3])
    
    logger.info(f"Generated {n_views} layered DIBR views from {len(layers)} layers")
    return views


def _forward_warp_rgba(source: np.ndarray, disparity: np.ndarray,
                       scale: float) -> Tuple[np.ndarray, np.ndarray]:
    """Forward warp RGBA image."""
    H, W = source.shape[:2]
    warped = np.zeros((H, W, 4), dtype=np.uint8)
    zbuffer = np.full((H, W), -np.inf, dtype=np.float32)
    hole_mask = np.ones((H, W), dtype=bool)
    
    shift = scale * disparity
    x_coords = np.arange(W, dtype=np.float32)
    
    for y in range(H):
        x_target = x_coords + shift[y]
        x_target_int = np.round(x_target).astype(np.int32)
        
        valid = (x_target_int >= 0) & (x_target_int < W)
        valid_indices = np.where(valid)[0]
        
        if len(valid_indices) == 0:
            continue
        
        # Only process pixels with alpha > 0
        has_alpha = source[y, valid_indices, 3] > 0
        valid_indices = valid_indices[has_alpha]
        
        depths = disparity[y]
        depth_order = np.argsort(depths[valid_indices])
        sorted_indices = valid_indices[depth_order]
        
        for x_src in sorted_indices:
            x_dst = x_target_int[x_src]
            d = depths[x_src]
            
            if d >= zbuffer[y, x_dst]:
                zbuffer[y, x_dst] = d
                warped[y, x_dst] = source[y, x_src]
                hole_mask[y, x_dst] = False
    
    return warped, hole_mask


def _alpha_composite(bg: np.ndarray, fg: np.ndarray) -> np.ndarray:
    """Alpha composite fg over bg (both RGBA uint8)."""
    fg_alpha = fg[:, :, 3:4].astype(np.float32) / 255.0
    bg_alpha = bg[:, :, 3:4].astype(np.float32) / 255.0
    
    out_alpha = fg_alpha + bg_alpha * (1 - fg_alpha)
    safe_alpha = np.maximum(out_alpha, 1e-6)
    
    out_rgb = (fg[:, :, :3].astype(np.float32) * fg_alpha + 
               bg[:, :, :3].astype(np.float32) * bg_alpha * (1 - fg_alpha)) / safe_alpha
    
    result = np.zeros_like(bg)
    result[:, :, :3] = np.clip(out_rgb, 0, 255).astype(np.uint8)
    result[:, :, 3] = np.clip(out_alpha * 255, 0, 255).astype(np.uint8)
    
    return result
