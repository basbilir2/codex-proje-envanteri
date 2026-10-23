"""Coordinate-based lenticular interlacing engine.

Implements physically-accurate interlacing by computing per-pixel
phase based on physical coordinates, supporting fractional pitch,
lens direction, skew, and sub-pixel RGB interlacing.
"""

import logging
import math
from typing import List, Optional, Tuple

import numpy as np

from utils.math_utils import (
    LensProfile, PrinterProfile, PrintJob,
    get_effective_lpi, get_lens_pitch_mm,
)

logger = logging.getLogger(__name__)


def compute_lens_normal(orientation: str = "vertical",
                        skew_degrees: float = 0.0) -> np.ndarray:
    """Compute unit normal vector perpendicular to lens lines.
    
    For vertical lenticules (standard 3D): normal is horizontal → (1, 0)
    For horizontal lenticules (flip): normal is vertical → (0, 1)
    Skew rotates the normal.
    
    Args:
        orientation: 'vertical' or 'horizontal'
        skew_degrees: Lens rotation in degrees (0 = perfectly aligned)
        
    Returns:
        Unit normal vector [nx, ny]
    """
    if orientation == "vertical":
        base_angle = 0.0  # Normal points along X (perpendicular to vertical lines)
    else:
        base_angle = 90.0  # Normal points along Y
    
    angle_rad = math.radians(base_angle + skew_degrees)
    return np.array([math.cos(angle_rad), math.sin(angle_rad)])


def interlace_standard(views: List[np.ndarray],
                       optical_lpi: float,
                       output_ppi: int,
                       orientation: str = "vertical",
                       registration_offset_mm: float = 0.0,
                       skew_degrees: float = 0.0,
                       flip_views: bool = False) -> np.ndarray:
    """Standard (whole-pixel) coordinate-based interlacing.
    
    Each output pixel is assigned to a view based on its physical
    position within the lenticule.
    
    φ(r) = fract((r - r0)·n̂ / p_lens)
    k(r) = floor(N × φ(r))
    
    Args:
        views: List of N view images, each (H, W, 3) uint8
        optical_lpi: Calibrated optical LPI
        output_ppi: Output raster PPI
        orientation: 'vertical' or 'horizontal'
        registration_offset_mm: Phase offset in mm
        skew_degrees: Lens skew angle in degrees
        flip_views: If True, reverse view order
        
    Returns:
        Interlaced image (H, W, 3) uint8
    """
    N = len(views)
    H, W = views[0].shape[:2]
    p_lens = 25.4 / optical_lpi  # mm per lenticule
    pixel_size = 25.4 / output_ppi  # mm per pixel
    
    n_hat = compute_lens_normal(orientation, skew_degrees)
    
    # View order
    if flip_views:
        views = views[::-1]
    
    output = np.zeros((H, W, 3), dtype=np.uint8)
    
    # For each pixel, compute physical position and phase
    # Vectorized implementation for speed
    j_coords = np.arange(W)  # column indices
    i_coords = np.arange(H)  # row indices
    
    # Physical position of pixel centers (mm)
    x_mm = (j_coords + 0.5) * pixel_size
    y_mm = (i_coords + 0.5) * pixel_size
    
    # Compute phase along lens normal direction
    # For each pixel (i, j): r = (x_mm[j], y_mm[i])
    # phase = fract(((r - r0) · n_hat) / p_lens)
    # r0 = (registration_offset_mm, 0)
    
    if abs(n_hat[1]) < 1e-6:
        # Pure horizontal normal (vertical lenticules) - common case
        # Phase depends only on x coordinate
        phase_1d = np.mod((x_mm - registration_offset_mm) * n_hat[0] / p_lens, 1.0)
        view_indices_1d = np.floor(phase_1d * N).astype(np.int32)
        view_indices_1d = np.clip(view_indices_1d, 0, N - 1)
        
        # Apply to all rows
        for k in range(N):
            cols = np.where(view_indices_1d == k)[0]
            if len(cols) > 0:
                output[:, cols, :] = views[k][:, cols, :]
    
    elif abs(n_hat[0]) < 1e-6:
        # Pure vertical normal (horizontal lenticules)
        phase_1d = np.mod((y_mm - 0.0) * n_hat[1] / p_lens, 1.0)
        view_indices_1d = np.floor(phase_1d * N).astype(np.int32)
        view_indices_1d = np.clip(view_indices_1d, 0, N - 1)
        
        for k in range(N):
            rows = np.where(view_indices_1d == k)[0]
            if len(rows) > 0:
                output[rows, :, :] = views[k][rows, :, :]
    
    else:
        # Skewed lens - full 2D computation
        xx, yy = np.meshgrid(x_mm, y_mm)
        dot = (xx - registration_offset_mm) * n_hat[0] + yy * n_hat[1]
        phase_2d = np.mod(dot / p_lens, 1.0)
        view_indices_2d = np.floor(phase_2d * N).astype(np.int32)
        view_indices_2d = np.clip(view_indices_2d, 0, N - 1)
        
        for k in range(N):
            mask = view_indices_2d == k
            output[mask] = views[k][mask]
    
    logger.info(f"Interlaced {N} views at {optical_lpi:.2f} LPI, {output_ppi} PPI")
    return output


def interlace_subpixel(views: List[np.ndarray],
                       optical_lpi: float,
                       output_ppi: int,
                       orientation: str = "vertical",
                       registration_offset_mm: float = 0.0,
                       skew_degrees: float = 0.0,
                       flip_views: bool = False) -> np.ndarray:
    """Sub-pixel interlacing with independent R, G, B view assignment.
    
    Each sub-pixel (R, G, B) is treated as having its own physical
    position within the pixel, effectively tripling horizontal resolution.
    
    For sub-pixel c ∈ {0=R, 1=G, 2=B}:
    r_sub_x = (j + (c + 0.5) / 3) × pixel_size
    
    Args:
        views: List of N view images, each (H, W, 3) uint8
        optical_lpi: Calibrated optical LPI
        output_ppi: Output raster PPI
        orientation: 'vertical' or 'horizontal'
        registration_offset_mm: Phase offset in mm
        skew_degrees: Lens skew angle in degrees
        flip_views: If True, reverse view order
        
    Returns:
        Interlaced image (H, W, 3) uint8
    """
    N = len(views)
    H, W = views[0].shape[:2]
    p_lens = 25.4 / optical_lpi
    pixel_size = 25.4 / output_ppi
    
    n_hat = compute_lens_normal(orientation, skew_degrees)
    
    if flip_views:
        views = views[::-1]
    
    # Stack views into array for efficient indexing
    view_stack = np.stack(views, axis=0)  # (N, H, W, 3)
    output = np.zeros((H, W, 3), dtype=np.uint8)
    
    if abs(n_hat[1]) < 1e-6:
        # Pure horizontal normal (common case) - vectorized
        for c in range(3):  # R, G, B
            # Sub-pixel physical position
            x_sub = (np.arange(W) + (c + 0.5) / 3) * pixel_size
            phase = np.mod((x_sub - registration_offset_mm) * n_hat[0] / p_lens, 1.0)
            view_idx = np.floor(phase * N).astype(np.int32)
            view_idx = np.clip(view_idx, 0, N - 1)
            
            # Assign each column's sub-pixel channel
            for j in range(W):
                output[:, j, c] = view_stack[view_idx[j], :, j, c]
    
    elif abs(n_hat[0]) < 1e-6:
        # Pure vertical normal
        for c in range(3):
            y_sub = (np.arange(H) + (c + 0.5) / 3) * pixel_size
            phase = np.mod(y_sub * n_hat[1] / p_lens, 1.0)
            view_idx = np.floor(phase * N).astype(np.int32)
            view_idx = np.clip(view_idx, 0, N - 1)
            
            for i in range(H):
                output[i, :, c] = view_stack[view_idx[i], i, :, c]
    
    else:
        # Skewed lens - full 2D per sub-pixel
        y_mm = (np.arange(H) + 0.5) * pixel_size
        for c in range(3):
            x_sub = (np.arange(W) + (c + 0.5) / 3) * pixel_size
            xx, yy = np.meshgrid(x_sub, y_mm)
            dot = (xx - registration_offset_mm) * n_hat[0] + yy * n_hat[1]
            phase = np.mod(dot / p_lens, 1.0)
            view_idx = np.floor(phase * N).astype(np.int32)
            view_idx = np.clip(view_idx, 0, N - 1)
            
            for k in range(N):
                mask = view_idx == k
                output[:, :, c][mask] = views[k][:, :, c][mask]
    
    logger.info(f"Sub-pixel interlaced {N} views at {optical_lpi:.2f} LPI, {output_ppi} PPI")
    return output


def interlace(views: List[np.ndarray],
              job: PrintJob,
              use_subpixel: Optional[bool] = None) -> np.ndarray:
    """Main interlacing entry point using print job configuration.
    
    Args:
        views: List of view images
        job: Print job specification
        use_subpixel: Override sub-pixel setting (None = use job setting)
        
    Returns:
        Interlaced image
    """
    optical_lpi = get_effective_lpi(job.lens_profile, job.viewing_distance_mm)
    output_ppi = job.printer_profile.output_raster_ppi
    orientation = job.lens_profile.orientation
    
    subpixel = use_subpixel if use_subpixel is not None else job.use_subpixel_interlacing
    
    if subpixel:
        return interlace_subpixel(
            views=views,
            optical_lpi=optical_lpi,
            output_ppi=output_ppi,
            orientation=orientation,
        )
    else:
        return interlace_standard(
            views=views,
            optical_lpi=optical_lpi,
            output_ppi=output_ppi,
            orientation=orientation,
        )


def create_interlacing_preview(views: List[np.ndarray],
                                optical_lpi: float,
                                output_ppi: int,
                                preview_scale: float = 0.25) -> np.ndarray:
    """Create a scaled-down interlacing preview for quick visualization.
    
    Args:
        views: List of view images
        optical_lpi: Calibrated optical LPI
        output_ppi: Output raster PPI
        preview_scale: Scale factor (0.25 = quarter size)
        
    Returns:
        Scaled interlaced preview image
    """
    import cv2
    
    # Scale down views
    scaled_views = []
    for v in views:
        h, w = v.shape[:2]
        new_h, new_w = int(h * preview_scale), int(w * preview_scale)
        scaled_views.append(cv2.resize(v, (new_w, new_h), interpolation=cv2.INTER_AREA))
    
    # Interlace at scaled PPI
    scaled_ppi = int(output_ppi * preview_scale)
    
    return interlace_standard(
        views=scaled_views,
        optical_lpi=optical_lpi,
        output_ppi=scaled_ppi,
    )
