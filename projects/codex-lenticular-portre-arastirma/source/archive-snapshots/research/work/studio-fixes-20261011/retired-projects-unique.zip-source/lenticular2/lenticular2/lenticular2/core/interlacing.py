"""Coordinate-based precision lenticular interlacing engine for Lenticular 2.

Implements physically-accurate interlacing supporting fractional pitch,
vertical and horizontal lens orientations, arbitrary skew angles,
measured registration offsets along the true optical normal, and CMYK flatbed safety.
"""

import logging
import math
from typing import List, Optional, Tuple
import numpy as np

from lenticular2.utils.math_utils import (
    LensProfile, PrinterProfile, PrintJob,
    get_effective_lpi, get_lens_pitch_mm,
)

logger = logging.getLogger(__name__)


def compute_lens_normal(orientation: str = "vertical",
                        skew_degrees: float = 0.0) -> np.ndarray:
    """Compute unit normal vector perpendicular to lenticular lens lines.
    
    For vertical lenticules (3D): base angle = 0 deg -> normal is along X (1, 0)
    For horizontal lenticules (Flip): base angle = 90 deg -> normal is along Y (0, 1)
    Skew rotates the normal.
    """
    base_angle = 0.0 if orientation == "vertical" else 90.0
    angle_rad = math.radians(base_angle + skew_degrees)
    return np.array([math.cos(angle_rad), math.sin(angle_rad)], dtype=np.float64)


def interlace_standard(views: List[np.ndarray],
                       optical_lpi: float,
                       output_ppi: int,
                       orientation: str = "vertical",
                       registration_offset_mm: float = 0.0,
                       skew_degrees: float = 0.0,
                       flip_views: bool = False) -> np.ndarray:
    """Standard (whole-pixel) coordinate-based interlacing.
    
    Assigns each output pixel to a specific view based on its physical location
    within the lenticule along the true lens normal.
    
    Formula:
      proj(x, y) = x_mm * n_x + y_mm * n_y - registration_offset_mm
      phase = fract(proj / p_lens)
      view_index = floor(N * phase)
    
    Args:
        views: List of N view images, each (H, W, 3) uint8
        optical_lpi: Calibrated or effective optical LPI
        output_ppi: Output raster PPI
        orientation: 'vertical' or 'horizontal'
        registration_offset_mm: Phase offset in mm along lens normal
        skew_degrees: Lens skew angle in degrees
        flip_views: Invert view sequence order
        
    Returns:
        Interlaced image (H, W, 3) uint8
    """
    if not views:
        raise ValueError("Views list cannot be empty.")
        
    N = len(views)
    H, W = views[0].shape[:2]
    p_lens = 25.4 / float(optical_lpi)  # Pitch in mm
    pixel_size = 25.4 / float(output_ppi)  # Pixel size in mm
    
    n_hat = compute_lens_normal(orientation, skew_degrees)
    
    if flip_views:
        views = views[::-1]
        
    output = np.zeros((H, W, 3), dtype=np.uint8)
    
    j_coords = np.arange(W, dtype=np.float64)  # columns (x)
    i_coords = np.arange(H, dtype=np.float64)  # rows (y)
    
    x_mm = (j_coords + 0.5) * pixel_size
    y_mm = (i_coords + 0.5) * pixel_size
    
    # 1. Pure vertical lenticules (no skew)
    if abs(n_hat[1]) < 1e-7:
        proj_1d = x_mm * n_hat[0] - registration_offset_mm
        phase_1d = np.mod(proj_1d / p_lens, 1.0)
        view_indices_1d = np.clip(np.floor(phase_1d * N).astype(np.int32), 0, N - 1)
        for k in range(N):
            cols = np.where(view_indices_1d == k)[0]
            if len(cols) > 0:
                output[:, cols, :] = views[k][:, cols, :]
                
    # 2. Pure horizontal lenticules (no skew) - correctly applies registration_offset_mm!
    elif abs(n_hat[0]) < 1e-7:
        proj_1d = y_mm * n_hat[1] - registration_offset_mm
        phase_1d = np.mod(proj_1d / p_lens, 1.0)
        view_indices_1d = np.clip(np.floor(phase_1d * N).astype(np.int32), 0, N - 1)
        for k in range(N):
            rows = np.where(view_indices_1d == k)[0]
            if len(rows) > 0:
                output[rows, :, :] = views[k][rows, :, :]
                
    # 3. Skewed lenticules (full 2D normal projection)
    else:
        xx, yy = np.meshgrid(x_mm, y_mm)
        proj_2d = xx * n_hat[0] + yy * n_hat[1] - registration_offset_mm
        phase_2d = np.mod(proj_2d / p_lens, 1.0)
        view_indices_2d = np.clip(np.floor(phase_2d * N).astype(np.int32), 0, N - 1)
        for k in range(N):
            mask = (view_indices_2d == k)
            output[mask] = views[k][mask]
            
    logger.info(f"Standard interlaced {N} views at {optical_lpi:.3f} LPI, offset={registration_offset_mm:.3f}mm, skew={skew_degrees:.2f}°")
    return output


def interlace_subpixel(views: List[np.ndarray],
                       optical_lpi: float,
                       output_ppi: int,
                       orientation: str = "vertical",
                       registration_offset_mm: float = 0.0,
                       skew_degrees: float = 0.0,
                       flip_views: bool = False) -> np.ndarray:
    """Sub-pixel RGB interlacing (intended ONLY for RGB displays / laser film).
    
    Warning: Do NOT use for CMYK UV Flatbed printing, as ink droplets overlap!
    """
    N = len(views)
    H, W = views[0].shape[:2]
    p_lens = 25.4 / float(optical_lpi)
    pixel_size = 25.4 / float(output_ppi)
    
    n_hat = compute_lens_normal(orientation, skew_degrees)
    
    if flip_views:
        views = views[::-1]
        
    output = np.zeros((H, W, 3), dtype=np.uint8)
    j_coords = np.arange(W, dtype=np.float64)
    i_coords = np.arange(H, dtype=np.float64)
    
    # Sub-pixel lateral offsets for R (c=0), G (c=1), B (c=2)
    subpixel_lateral_offsets = np.array([-1.0 / 3.0, 0.0, 1.0 / 3.0]) * pixel_size
    
    if abs(n_hat[1]) < 1e-7:
        base_x = (j_coords + 0.5) * pixel_size
        for c in range(3):
            x_c = base_x + subpixel_lateral_offsets[c]
            proj = x_c * n_hat[0] - registration_offset_mm
            phase = np.mod(proj / p_lens, 1.0)
            v_idx = np.clip(np.floor(phase * N).astype(np.int32), 0, N - 1)
            for k in range(N):
                cols = np.where(v_idx == k)[0]
                if len(cols) > 0:
                    output[:, cols, c] = views[k][:, cols, c]
    else:
        xx, yy = np.meshgrid((j_coords + 0.5) * pixel_size, (i_coords + 0.5) * pixel_size)
        for c in range(3):
            sub_x = xx + subpixel_lateral_offsets[c] * n_hat[0]
            sub_y = yy + subpixel_lateral_offsets[c] * n_hat[1]
            proj = sub_x * n_hat[0] + sub_y * n_hat[1] - registration_offset_mm
            phase = np.mod(proj / p_lens, 1.0)
            v_idx = np.clip(np.floor(phase * N).astype(np.int32), 0, N - 1)
            for k in range(N):
                mask = (v_idx == k)
                output[:, :, c][mask] = views[k][:, :, c][mask]
                
    return output


def interlace(views: List[np.ndarray],
              job: PrintJob,
              use_subpixel: Optional[bool] = None,
              registration_offset_mm: Optional[float] = None,
              skew_degrees: Optional[float] = None,
              flip_views: Optional[bool] = None) -> np.ndarray:
    """Main production interlacing entry point for Lenticular 2.
    
    Properly forwards all registration, skew, and view flip parameters from PrintJob.
    Defaults to safe whole-pixel interlacing suitable for UV flatbeds.
    """
    optical_lpi = get_effective_lpi(job.lens_profile, job.viewing_distance_mm)
    output_ppi = job.printer_profile.output_raster_ppi
    orientation = job.lens_profile.orientation
    
    subpixel = use_subpixel if use_subpixel is not None else job.use_subpixel_interlacing
    offset = registration_offset_mm if registration_offset_mm is not None else job.registration_offset_mm
    skew = skew_degrees if skew_degrees is not None else job.skew_degrees
    flip = flip_views if flip_views is not None else job.flip_views
    
    if subpixel:
        logger.warning("Subpixel interlacing enabled: ensure output is intended for RGB display, not CMYK flatbed.")
        return interlace_subpixel(
            views=views,
            optical_lpi=optical_lpi,
            output_ppi=output_ppi,
            orientation=orientation,
            registration_offset_mm=offset,
            skew_degrees=skew,
            flip_views=flip,
        )
    else:
        return interlace_standard(
            views=views,
            optical_lpi=optical_lpi,
            output_ppi=output_ppi,
            orientation=orientation,
            registration_offset_mm=offset,
            skew_degrees=skew,
            flip_views=flip,
        )


def create_interlacing_preview(views: List[np.ndarray],
                               optical_lpi: float,
                               output_ppi: int,
                               preview_scale: float = 0.25) -> np.ndarray:
    """Create a scaled-down interlacing preview for quick inspection."""
    import cv2
    scaled_views = []
    for v in views:
        h, w = v.shape[:2]
        new_h = max(16, int(h * preview_scale))
        new_w = max(16, int(w * preview_scale))
        scaled_views.append(cv2.resize(v, (new_w, new_h), interpolation=cv2.INTER_AREA))
        
    scaled_ppi = max(50, int(output_ppi * preview_scale))
    return interlace_standard(
        views=scaled_views,
        optical_lpi=optical_lpi,
        output_ppi=scaled_ppi,
    )
