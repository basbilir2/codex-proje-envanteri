"""Image I/O and common operations for the lenticular pipeline."""

import logging
from pathlib import Path
from typing import Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def load_image(path: Union[str, Path], mode: str = "rgb") -> np.ndarray:
    """Load an image file.
    
    Args:
        path: Path to image file
        mode: 'rgb' (default), 'rgba', 'gray', 'gray16'
        
    Returns:
        NumPy array in specified mode
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file can't be read as image
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
    
    if mode == "rgba":
        if img.shape[2] == 3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        return cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
    else:  # rgb
        if len(img.shape) == 2:
            return cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA)
            return img[:, :, :3]
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def save_image(img: np.ndarray, path: Union[str, Path], 
               quality: int = 95, ppi: Optional[int] = None) -> None:
    """Save an image with optional PPI metadata.
    
    Supports PNG, TIFF, JPEG formats (detected from extension).
    For TIFF, uses LZW compression.
    
    Args:
        img: Image array (RGB, RGBA, or grayscale)
        path: Output path
        quality: JPEG quality (ignored for PNG/TIFF)
        ppi: Pixels per inch metadata (optional)
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ext = path.suffix.lower()
    
    if ext in ('.tif', '.tiff'):
        # Use tifffile for proper TIFF with PPI
        try:
            import tifffile
            # tifffile expects RGB order
            resolution = (ppi, ppi) if ppi else None
            tifffile.imwrite(
                str(path), img,
                compression='lzw',
                resolution=resolution,
                resolutionunit=2 if ppi else None,  # 2 = inches
            )
            logger.info(f"Saved TIFF: {path} ({img.shape})")
            return
        except ImportError:
            logger.warning("tifffile not available, falling back to PIL for TIFF")
    
    # Use PIL for other formats and fallback
    if len(img.shape) == 2:
        pil_img = Image.fromarray(img, mode='L')
    elif img.shape[2] == 4:
        pil_img = Image.fromarray(img, mode='RGBA')
    else:
        pil_img = Image.fromarray(img, mode='RGB')
    
    save_kwargs = {}
    if ext in ('.jpg', '.jpeg'):
        save_kwargs['quality'] = quality
        save_kwargs['subsampling'] = 0  # 4:4:4
    elif ext == '.png':
        save_kwargs['compress_level'] = 6
    
    if ppi:
        pil_img.info['dpi'] = (ppi, ppi)
        save_kwargs['dpi'] = (ppi, ppi)
    
    pil_img.save(str(path), **save_kwargs)
    logger.info(f"Saved {ext}: {path} ({img.shape})")


def resize_to_output(img: np.ndarray, width_px: int, height_px: int,
                     interpolation: int = cv2.INTER_LANCZOS4) -> np.ndarray:
    """Resize image to exact output dimensions.
    
    Args:
        img: Input image
        width_px: Target width in pixels
        height_px: Target height in pixels
        interpolation: OpenCV interpolation method
        
    Returns:
        Resized image
    """
    return cv2.resize(img, (width_px, height_px), interpolation=interpolation)


def normalize_depth(depth: np.ndarray, white_near: bool = True) -> np.ndarray:
    """Normalize depth map to [0, 1] float32 range.
    
    Convention: white (1.0) = near/foreground, black (0.0) = far/background.
    Auto-detects convention if possible (assumes foreground objects are larger/central).
    
    Args:
        depth: Input depth map (any bit depth)
        white_near: If True, ensure white=near convention. If False, white=far.
        
    Returns:
        Normalized depth map as float32 in [0, 1]
    """
    depth_f = depth.astype(np.float32)
    d_min, d_max = depth_f.min(), depth_f.max()
    
    if d_max - d_min < 1e-7:
        logger.warning("Depth map has no range (flat scene)")
        return np.full_like(depth_f, 0.5)
    
    normalized = (depth_f - d_min) / (d_max - d_min)
    
    # Detect convention: if center region is brighter, likely white=near already
    h, w = normalized.shape[:2]
    center = normalized[h//4:3*h//4, w//4:3*w//4]
    border_top = normalized[:h//8, :]
    border_bot = normalized[7*h//8:, :]
    
    center_mean = center.mean()
    border_mean = (border_top.mean() + border_bot.mean()) / 2
    
    # If center is darker than borders, convention is likely inverted
    detected_white_near = center_mean > border_mean
    
    if white_near and not detected_white_near:
        logger.info("Depth convention detected as white=far, inverting to white=near")
        normalized = 1.0 - normalized
    elif not white_near and detected_white_near:
        logger.info("Depth convention detected as white=near, inverting to white=far")
        normalized = 1.0 - normalized
    
    return normalized


def create_animation_frames(views: list, loop: bool = True) -> list:
    """Create animation frames from multi-view images for preview.
    
    Creates a forward-backward loop for wiggle/look-around effect.
    
    Args:
        views: List of view images (numpy arrays)
        loop: If True, creates forward-backward loop
        
    Returns:
        List of frames for animation
    """
    if loop:
        return views + views[-2:0:-1]  # Forward then backward (exclude endpoints duplicate)
    return views


def save_animation(frames: list, path: Union[str, Path], 
                   fps: int = 15, duration_ms: Optional[int] = None) -> None:
    """Save frames as animated GIF.
    
    Args:
        frames: List of numpy arrays (RGB)
        path: Output GIF path
        fps: Frames per second (used if duration_ms is None)
        duration_ms: Duration per frame in ms (overrides fps)
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if duration_ms is None:
        duration_ms = int(1000 / fps)
    
    pil_frames = [Image.fromarray(f) for f in frames]
    pil_frames[0].save(
        str(path),
        save_all=True,
        append_images=pil_frames[1:],
        duration=duration_ms,
        loop=0  # Infinite loop
    )
    logger.info(f"Saved animation: {path} ({len(frames)} frames, {duration_ms}ms/frame)")


def compute_depth_histogram(depth_normalized: np.ndarray, bins: int = 256) -> dict:
    """Analyze depth map distribution for scene characterization.
    
    Args:
        depth_normalized: Normalized depth map [0, 1]
        bins: Number of histogram bins
        
    Returns:
        Dictionary with histogram data and scene analysis
    """
    hist, bin_edges = np.histogram(depth_normalized, bins=bins, range=(0, 1))
    hist_normalized = hist / hist.sum()
    
    mean = float(depth_normalized.mean())
    std = float(depth_normalized.std())
    
    # Scene characterization
    if std < 0.15:
        scene_type = "flat"
        advice = "Low depth variation — 3D effect will be limited"
    elif std > 0.3:
        scene_type = "deep"
        advice = "High depth variation — strong 3D potential"
    else:
        scene_type = "moderate"
        advice = "Moderate depth — good 3D potential"
    
    # Detect bimodal distribution (FG/BG separation)
    from scipy import signal
    smoothed = np.convolve(hist_normalized, np.ones(5)/5, mode='same')
    peaks, _ = signal.find_peaks(smoothed, height=0.005, distance=bins//8)
    
    if len(peaks) >= 2:
        scene_type = "bimodal"
        advice = "Clear FG/BG separation — excellent 3D potential"
    
    return {
        "histogram": hist_normalized.tolist(),
        "bin_edges": bin_edges.tolist(),
        "mean": mean,
        "std": std,
        "scene_type": scene_type,
        "advice": advice,
        "n_peaks": len(peaks),
    }
