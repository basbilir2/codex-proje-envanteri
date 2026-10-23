"""Depth map optimization and post-processing pipeline for Lenticular 2.

Handles native float32 edge-preserving bilateral filtering (no 8-bit quantization),
pure box-filter guided edge alignment, and single-pass depth curves.
"""

import logging
from typing import Optional, Dict, Any, Tuple
import cv2
import numpy as np

from lenticular2.utils.image_utils import normalize_depth, compute_depth_histogram

logger = logging.getLogger(__name__)


def guided_filter_numpy(guide: np.ndarray, src: np.ndarray, radius: int = 8, eps: float = 0.01) -> np.ndarray:
    """Pure OpenCV/NumPy box-filter implementation of He et al. Guided Filter.
    
    Guarantees operation even when opencv-contrib-python is not installed.
    """
    I = guide.astype(np.float32)
    p = src.astype(np.float32)
    ksize = (2 * radius + 1, 2 * radius + 1)
    
    mean_I = cv2.boxFilter(I, cv2.CV_32F, ksize)
    mean_p = cv2.boxFilter(p, cv2.CV_32F, ksize)
    mean_Ip = cv2.boxFilter(I * p, cv2.CV_32F, ksize)
    cov_Ip = mean_Ip - mean_I * mean_p
    
    mean_II = cv2.boxFilter(I * I, cv2.CV_32F, ksize)
    var_I = mean_II - mean_I * mean_I
    
    a = cov_Ip / (var_I + eps)
    b = mean_p - a * mean_I
    
    mean_a = cv2.boxFilter(a, cv2.CV_32F, ksize)
    mean_b = cv2.boxFilter(b, cv2.CV_32F, ksize)
    
    q = mean_a * I + mean_b
    return np.clip(q, 0.0, 1.0).astype(np.float32)


class DepthOptimizer:
    """Optimizes raw depth maps with float32 precision for Lenticular 2."""
    
    def __init__(self,
                 bilateral_d: int = 9,
                 bilateral_sigma_color: float = 0.15,  # Scaled for [0, 1] float range
                 bilateral_sigma_space: float = 9.0,
                 guided_radius: int = 8,
                 guided_eps: float = 0.01):
        self.bilateral_d = bilateral_d
        self.bilateral_sigma_color = bilateral_sigma_color
        self.bilateral_sigma_space = bilateral_sigma_space
        self.guided_radius = guided_radius
        self.guided_eps = guided_eps
    
    def optimize(self, depth_raw: np.ndarray,
                 rgb_guide: Optional[np.ndarray] = None,
                 denoise: bool = True,
                 edge_refine: bool = True,
                 apply_curve: bool = False,
                 depth_curve: str = "linear",
                 gamma: float = 1.0,
                 auto_detect_depth_polarity: bool = False) -> np.ndarray:
        """Run the full depth optimization pipeline in float32.
        
        Args:
            depth_raw: Raw input depth (float, uint8, uint16)
            rgb_guide: Optional RGB guide image for edge refinement
            denoise: Apply native float32 bilateral filter
            edge_refine: Apply guided filter to align depth edges to RGB boundaries
            apply_curve: Set True ONLY if depth curve should be applied here (avoids double curve)
            depth_curve: 'linear', 'gamma', 'sigmoid'
            gamma: Gamma exponent
            auto_detect_depth_polarity: Heuristic polarity toggle (default False)
            
        Returns:
            Optimized float32 depth map in [0.0, 1.0] range
        """
        # Step 1: Normalize safely
        depth = normalize_depth(
            depth_raw,
            white_near=True,
            auto_detect_depth_polarity=auto_detect_depth_polarity
        )
        
        # Step 2: Denoise natively in float32 without 8-bit quantization
        if denoise:
            depth = self._bilateral_denoise_f32(depth)
        
        # Step 3: Edge refinement with RGB guide
        if edge_refine and rgb_guide is not None:
            depth = self._guided_filter(depth, rgb_guide)
        
        # Step 4: Optional depth curve (default is False to prevent double-gamma)
        if apply_curve and depth_curve != "linear":
            depth = self._apply_curve(depth, depth_curve, gamma)
            
        return np.clip(depth, 0.0, 1.0).astype(np.float32)
    
    def _bilateral_denoise_f32(self, depth: np.ndarray) -> np.ndarray:
        """Native float32 bilateral filtering preserving micro-gradients."""
        depth_f32 = depth.astype(np.float32)
        filtered = cv2.bilateralFilter(
            depth_f32,
            self.bilateral_d,
            self.bilateral_sigma_color,
            self.bilateral_sigma_space
        )
        return filtered.astype(np.float32)
    
    def _guided_filter(self, depth: np.ndarray, rgb_guide: np.ndarray) -> np.ndarray:
        """Align depth boundaries to color edges."""
        if len(rgb_guide.shape) == 3:
            guide_gray = cv2.cvtColor(rgb_guide, cv2.COLOR_RGB2GRAY)
        else:
            guide_gray = rgb_guide
        guide_f = guide_gray.astype(np.float32) / 255.0
        
        if guide_f.shape != depth.shape:
            guide_f = cv2.resize(guide_f, (depth.shape[1], depth.shape[0]), interpolation=cv2.INTER_LINEAR)
        
        try:
            if hasattr(cv2, "ximgproc") and hasattr(cv2.ximgproc, "guidedFilter"):
                return cv2.ximgproc.guidedFilter(
                    guide=guide_f, src=depth,
                    radius=self.guided_radius, eps=self.guided_eps
                )
        except Exception:
            pass
        
        # Robust fallback using OpenCV boxFilter implementation
        return guided_filter_numpy(guide_f, depth, self.guided_radius, self.guided_eps)
    
    def _apply_curve(self, depth: np.ndarray, curve: str, gamma: float) -> np.ndarray:
        """Apply depth curve redistribution."""
        if curve == "gamma" and abs(gamma - 1.0) > 1e-4:
            return np.power(np.clip(depth, 0.0, 1.0), gamma)
        elif curve == "sigmoid":
            beta = 5.0
            centered = depth - 0.5
            return 1.0 / (1.0 + np.exp(-beta * centered))
        return depth
    
    def analyze(self, depth_normalized: np.ndarray) -> Dict[str, Any]:
        """Analyze depth statistics."""
        counts, edges = compute_depth_histogram(depth_normalized)
        return {
            "min": float(depth_normalized.min()),
            "max": float(depth_normalized.max()),
            "mean": float(depth_normalized.mean()),
            "median": float(np.median(depth_normalized)),
            "std": float(depth_normalized.std()),
            "histogram": {"counts": counts.tolist(), "edges": edges.tolist()},
        }
