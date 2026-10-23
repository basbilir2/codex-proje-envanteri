"""Image I/O and processing utilities for Lenticular 2.

Handles multi-format loading (2D grayscale, RGB, RGBA, 16-bit depth, TIFF/PNG),
depth normalization without destructive auto-inversion, and metadata preservation.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple, Union, List

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def load_image(path: Union[str, Path], mode: str = "rgb") -> np.ndarray:
    """Load an image file safely handling any channel format.
    
    Args:
        path: Path to image file
        mode: 'rgb' (default), 'rgba', 'gray', 'gray16'
        
    Returns:
        NumPy array in specified mode:
        - 'rgb': (H, W, 3) uint8
        - 'rgba': (H, W, 4) uint8
        - 'gray': (H, W) uint8
        - 'gray16': (H, W) uint16 or uint8
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    
    if mode == "gray16":
        img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError(f"Failed to read image: {path}")
        if len(img.shape) == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img
    
    if mode == "gray":
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Failed to read image: {path}")
        return img
    
    img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"Failed to read image: {path}")
    
    ndim = len(img.shape)
    
    if mode == "rgba":
        if ndim == 2:
            return cv2.cvtColor(img, cv2.COLOR_GRAY2RGBA)
        elif ndim == 3:
            ch = img.shape[2]
            if ch == 3:
                return cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
            elif ch == 4:
                return cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
            else:
                return cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2RGBA)
        else:
            raise ValueError(f"Unsupported image dimensions: {img.shape}")
    
    else:  # rgb
        if ndim == 2:
            return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        elif ndim == 3:
            ch = img.shape[2]
            if ch == 4:
                return cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
            elif ch == 3:
                return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            else:
                return cv2.cvtColor(img[:, :, :3], cv2.COLOR_BGR2RGB)
        else:
            raise ValueError(f"Unsupported image dimensions: {img.shape}")


def save_image(img: np.ndarray, path: Union[str, Path],
               quality: int = 95, ppi: Optional[int] = None) -> None:
    """Save an image with optional DPI/PPI metadata and lossless TIFF support."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix.lower()
    
    if ext in ('.tif', '.tiff'):
        try:
            import tifffile
            resolution = (ppi, ppi) if ppi else None
            tifffile.imwrite(
                str(path), img,
                compression='zlib',  # standard zlib / deflate supported without imagecodecs
                resolution=resolution,
                resolutionunit=2 if ppi else None,  # 2 = inch
            )
            logger.info(f"Saved TIFF: {path} ({img.shape})")
            return
        except Exception as e:
            logger.warning(f"tifffile failed ({e}), falling back to Pillow for TIFF.")
    
    if len(img.shape) == 2:
        pil_img = Image.fromarray(img, mode='L' if img.dtype == np.uint8 else 'I;16')
    elif img.shape[2] == 4:
        pil_img = Image.fromarray(img, mode='RGBA')
    else:
        pil_img = Image.fromarray(img, mode='RGB')
    
    save_kwargs = {}
    if ext in ('.jpg', '.jpeg'):
        save_kwargs['quality'] = quality
        save_kwargs['subsampling'] = 0
    elif ext == '.png':
        save_kwargs['compress_level'] = 6
    elif ext in ('.tif', '.tiff'):
        save_kwargs['compression'] = 'tiff_deflate'
    
    if ppi:
        pil_img.info['dpi'] = (ppi, ppi)
        save_kwargs['dpi'] = (ppi, ppi)
    
    pil_img.save(str(path), **save_kwargs)
    logger.info(f"Saved image: {path} ({img.shape})")


def resize_to_output(img: np.ndarray, width_px: int, height_px: int,
                     interpolation: int = cv2.INTER_LANCZOS4) -> np.ndarray:
    """Resize image to exact output dimensions."""
    return cv2.resize(img, (width_px, height_px), interpolation=interpolation)


def normalize_depth(depth: np.ndarray,
                    white_near: bool = True,
                    auto_detect_depth_polarity: bool = False,
                    invert: bool = False) -> np.ndarray:
    """Normalize depth map to [0.0, 1.0] float32 range.
    
    Standard convention: white (1.0) = near / foreground, black (0.0) = far / background.
    
    Args:
        depth: Input depth map (float, uint8, or uint16)
        white_near: Target convention. If True, 1.0 = near. If False, 0.0 = near.
        auto_detect_depth_polarity: If False (DEFAULT), relies strictly on white_near & invert.
                                   If True, inspects image heuristics.
        invert: Explicit user inversion toggle.
        
    Returns:
        Normalized depth map as float32 in [0.0, 1.0].
    """
    if len(depth.shape) == 3:
        depth = cv2.cvtColor(depth, cv2.COLOR_BGR2GRAY) if depth.shape[2] == 3 else depth[:, :, 0]
    
    depth_f = depth.astype(np.float32)
    d_min, d_max = float(depth_f.min()), float(depth_f.max())
    
    if d_max - d_min < 1e-7:
        logger.warning("Depth map has near zero dynamic range (flat scene).")
        return np.full_like(depth_f, 0.5)
    
    normalized = (depth_f - d_min) / (d_max - d_min)
    
    if auto_detect_depth_polarity:
        h, w = normalized.shape[:2]
        center = normalized[h//4:3*h//4, w//4:3*w//4]
        border_top = normalized[:h//8, :]
        border_bot = normalized[7*h//8:, :]
        center_mean = float(center.mean()) if center.size > 0 else 0.5
        border_mean = float((border_top.mean() + border_bot.mean()) / 2.0)
        detected_white_near = center_mean > border_mean
        
        if white_near and not detected_white_near:
            logger.info("Auto-polarity: Inverting depth map to enforce white=near convention.")
            normalized = 1.0 - normalized
        elif not white_near and detected_white_near:
            normalized = 1.0 - normalized
    else:
        if not white_near:
            normalized = 1.0 - normalized
    
    if invert:
        normalized = 1.0 - normalized
        
    return normalized.astype(np.float32)


def create_animation_frames(views: List[np.ndarray], loop: bool = True) -> List[np.ndarray]:
    """Create look-around animation frames from multi-view sequence."""
    if len(views) <= 1:
        return views
    if loop:
        return views + views[-2:0:-1]
    return views


def save_animation(frames: List[np.ndarray], path: Union[str, Path],
                   fps: int = 15, duration_ms: Optional[int] = None) -> None:
    """Save frames as animated GIF for preview."""
    if not frames:
        return
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    dur = duration_ms if duration_ms is not None else int(1000.0 / fps)
    pil_frames = [Image.fromarray(f) for f in frames]
    pil_frames[0].save(
        str(path),
        save_all=True,
        append_images=pil_frames[1:],
        duration=dur,
        loop=0
    )
    logger.info(f"Saved animation preview: {path}")


def compute_depth_histogram(depth_normalized: np.ndarray, bins: int = 50) -> Tuple[np.ndarray, np.ndarray]:
    """Compute histogram of depth values."""
    counts, edges = np.histogram(depth_normalized, bins=bins, range=(0.0, 1.0))
    return counts, edges
