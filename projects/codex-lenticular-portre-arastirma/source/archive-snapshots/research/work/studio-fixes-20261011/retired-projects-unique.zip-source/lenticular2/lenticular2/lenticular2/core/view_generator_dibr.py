"""High-performance Depth-Image Based Rendering (DIBR) engine for Lenticular 2.

Replaces slow Python pixel loops with vectorized C++ warping (cv2.remap),
bidirectional occlusion detection, and clean boundary inpainting.
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
                        interpolation: int = cv2.INTER_LANCZOS4) -> List[np.ndarray]:
    """Generate multi-view images using high-performance vectorized DIBR.
    
    Args:
        source_image: Source photograph (H, W, 3) uint8
        disparity_map: Disparity map in pixels (H, W) float32 (positive=near, negative=far)
        n_views: Total number of views to render
        fill_holes: Inpaint disocclusion regions
        interpolation: OpenCV interpolation mode (default cv2.INTER_LANCZOS4)
        
    Returns:
        List of N view images, each (H, W, 3) uint8
    """
    H, W = source_image.shape[:2]
    views: List[np.ndarray] = []
    
    # Pre-generate base pixel coordinate grids
    x_grid, y_grid = np.meshgrid(np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32))
    
    disp_f32 = disparity_map.astype(np.float32)
    # Compute horizontal disparity gradient to detect stretching/disocclusion
    grad_x = cv2.Sobel(disp_f32, cv2.CV_32F, 1, 0, ksize=3) / 8.0
    
    for k in range(n_views):
        s_k = (k / (n_views - 1.0)) - 0.5 if n_views > 1 else 0.0
        
        # Backward coordinate mapping:
        # To find color for pixel (x, y) in view k:
        # x_source = x - s_k * disparity(x, y)
        shift = s_k * disp_f32
        map_x = (x_grid - shift).astype(np.float32)
        map_y = y_grid.copy()
        
        # Warp with C++ accelerated remap
        warped = cv2.remap(
            source_image, map_x, map_y,
            interpolation=interpolation,
            borderMode=cv2.BORDER_REFLECT_101
        )
        
        # Disocclusion hole detection
        # Disocclusion occurs when foreground moves laterally exposing unseen background
        if fill_holes and abs(s_k) > 1e-4:
            # When s_k > 0 (right camera), disocclusion appears where disparity drops from left to right (grad_x < -0.3)
            # When s_k < 0 (left camera), disocclusion appears where disparity rises from left to right (grad_x > 0.3)
            stretch = s_k * grad_x
            hole_mask = (stretch > 0.45).astype(np.uint8) * 255
            
            # Morphological cleanup on hole mask
            if hole_mask.any():
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                hole_mask = cv2.dilate(hole_mask, kernel, iterations=1)
                
                # Inpaint holes using Navier-Stokes / Telea method
                warped = cv2.inpaint(warped, hole_mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
        
        views.append(warped)
        logger.debug(f"View {k+1}/{n_views}: s_k={s_k:.3f} rendered.")
    
    logger.info(f"Rendered {n_views} DIBR views using vectorized C++ remap.")
    return views


def generate_views_forward_splat(source_image: np.ndarray,
                                 disparity_map: np.ndarray,
                                 n_views: int) -> List[np.ndarray]:
    """Forward splatting alternative with vectorized z-buffering.
    
    Useful for verification and comparison against backward warping.
    """
    H, W = source_image.shape[:2]
    views = []
    
    x_coords = np.arange(W, dtype=np.float32)
    
    for k in range(n_views):
        s_k = (k / (n_views - 1.0)) - 0.5 if n_views > 1 else 0.0
        shift = s_k * disparity_map
        
        warped = np.zeros_like(source_image)
        zbuffer = np.full((H, W), -1e9, dtype=np.float32)
        
        for y in range(H):
            x_target = np.round(x_coords + shift[y]).astype(np.int32)
            valid = (x_target >= 0) & (x_target < W)
            if not valid.any():
                continue
            
            src_x = np.where(valid)[0]
            dst_x = x_target[valid]
            d = disparity_map[y, src_x]
            
            # Sort far to near so near overwrites
            order = np.argsort(d)
            for idx in order:
                sx = src_x[idx]
                dx = dst_x[idx]
                depth_val = d[idx]
                if depth_val >= zbuffer[y, dx]:
                    zbuffer[y, dx] = depth_val
                    warped[y, dx] = source_image[y, sx]
        
        # Simple horizontal gap fill
        mask = (zbuffer == -1e9).astype(np.uint8) * 255
        if mask.any():
            warped = cv2.inpaint(warped, mask, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
            
        views.append(warped)
        
    return views
