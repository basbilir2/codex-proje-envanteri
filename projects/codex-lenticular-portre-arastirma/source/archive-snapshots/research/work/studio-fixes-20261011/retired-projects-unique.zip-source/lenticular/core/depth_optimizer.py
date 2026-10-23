"""Depth map optimization and post-processing pipeline.

Handles normalization, edge-preserving denoising, guided filtering
(depth edges aligned to RGB edges), depth curve application,
and scene analysis.
"""

import logging
from typing import Optional, Tuple, Dict

import cv2
import numpy as np

from utils.image_utils import normalize_depth, compute_depth_histogram

logger = logging.getLogger(__name__)


class DepthOptimizer:
    """Optimizes raw depth maps for lenticular multi-view generation."""
    
    def __init__(self, bilateral_d: int = 9, bilateral_sigma_color: float = 75.0,
                 bilateral_sigma_space: float = 75.0,
                 guided_radius: int = 8, guided_eps: float = 0.01):
        """Initialize optimizer with filter parameters.
        
        Args:
            bilateral_d: Bilateral filter diameter
            bilateral_sigma_color: Bilateral filter color sigma
            bilateral_sigma_space: Bilateral filter space sigma
            guided_radius: Guided filter radius
            guided_eps: Guided filter regularization
        """
        self.bilateral_d = bilateral_d
        self.bilateral_sigma_color = bilateral_sigma_color
        self.bilateral_sigma_space = bilateral_sigma_space
        self.guided_radius = guided_radius
        self.guided_eps = guided_eps
    
    def optimize(self, depth_raw: np.ndarray, 
                 rgb_guide: Optional[np.ndarray] = None,
                 denoise: bool = True,
                 edge_refine: bool = True,
                 depth_curve: str = "linear",
                 gamma: float = 1.0) -> np.ndarray:
        """Run the full depth optimization pipeline.
        
        Pipeline:
        1. Normalize to [0, 1] with convention standardization
        2. Edge-preserving noise reduction (bilateral filter)
        3. Edge refinement via guided filter (align depth edges to RGB)
        4. Depth curve application (linear, gamma, sigmoid)
        
        Args:
            depth_raw: Raw depth map from estimator (any bit depth)
            rgb_guide: RGB guide image for guided filtering (optional)
            denoise: Whether to apply bilateral denoising
            edge_refine: Whether to apply guided filter edge refinement
            depth_curve: Curve function: 'linear', 'gamma', 'sigmoid'
            gamma: Gamma value for gamma curve
            
        Returns:
            Optimized depth map as float32 in [0, 1]
        """
        # Step 1: Normalize
        depth = normalize_depth(depth_raw, white_near=True)
        logger.info(f"Depth normalized: range [{depth.min():.3f}, {depth.max():.3f}]")
        
        # Step 2: Edge-preserving denoising
        if denoise:
            depth = self._bilateral_denoise(depth)
            logger.info("Bilateral denoising applied")
        
        # Step 3: Edge refinement with RGB guide
        if edge_refine and rgb_guide is not None:
            depth = self._guided_filter(depth, rgb_guide)
            logger.info("Guided filter edge refinement applied")
        
        # Step 4: Depth curve
        if depth_curve != "linear":
            depth = self._apply_curve(depth, depth_curve, gamma)
            logger.info(f"Depth curve applied: {depth_curve}" + 
                       (f" (gamma={gamma})" if depth_curve == "gamma" else ""))
        
        return depth
    
    def _bilateral_denoise(self, depth: np.ndarray) -> np.ndarray:
        """Apply edge-preserving bilateral filter.
        
        Preserves depth discontinuities (object boundaries) while
        smoothing noise within continuous surfaces.
        """
        # Convert to uint8 for bilateral (or use float version)
        depth_u8 = (depth * 255).astype(np.uint8)
        filtered = cv2.bilateralFilter(
            depth_u8, 
            self.bilateral_d, 
            self.bilateral_sigma_color, 
            self.bilateral_sigma_space
        )
        return filtered.astype(np.float32) / 255.0
    
    def _guided_filter(self, depth: np.ndarray, 
                       rgb_guide: np.ndarray) -> np.ndarray:
        """Align depth edges to RGB image edges using guided filter.
        
        This prevents 'halo' artifacts where depth boundaries don't
        align with actual object boundaries in the image.
        """
        try:
            # Convert guide to grayscale float
            if len(rgb_guide.shape) == 3:
                guide_gray = cv2.cvtColor(rgb_guide, cv2.COLOR_RGB2GRAY)
            else:
                guide_gray = rgb_guide
            guide_f = guide_gray.astype(np.float32) / 255.0
            
            # Resize guide to match depth if needed
            if guide_f.shape != depth.shape:
                guide_f = cv2.resize(guide_f, (depth.shape[1], depth.shape[0]),
                                     interpolation=cv2.INTER_LINEAR)
            
            filtered = cv2.ximgproc.guidedFilter(
                guide=guide_f, src=depth,
                radius=self.guided_radius, eps=self.guided_eps
            )
            return filtered
        except AttributeError:
            logger.warning("cv2.ximgproc not available (install opencv-contrib-python). "
                          "Skipping guided filter.")
            return depth
    
    def _apply_curve(self, depth: np.ndarray, 
                     curve: str, gamma: float) -> np.ndarray:
        """Apply depth redistribution curve.
        
        - gamma < 1: Enhances foreground detail
        - gamma > 1: Enhances background detail
        - sigmoid: Smooth S-curve compression
        """
        if curve == "gamma":
            return np.power(depth, gamma)
        elif curve == "sigmoid":
            beta = 5.0
            centered = depth - 0.5
            return 1.0 / (1.0 + np.exp(-beta * centered))
        return depth
    
    def analyze(self, depth_normalized: np.ndarray) -> Dict:
        """Analyze depth map characteristics for scene understanding.
        
        Returns histogram analysis, scene type classification,
        and recommendations.
        
        Args:
            depth_normalized: Normalized depth map [0, 1]
            
        Returns:
            Analysis dictionary with histogram data and recommendations
        """
        analysis = compute_depth_histogram(depth_normalized)
        
        # Add layer separation recommendation
        if analysis["n_peaks"] >= 2:
            analysis["layer_recommendation"] = (
                f"Bimodal distribution detected ({analysis['n_peaks']} peaks). "
                f"Layer separation recommended for better 3D quality."
            )
        elif analysis["std"] < 0.15:
            analysis["layer_recommendation"] = (
                "Flat scene detected. Layer separation may not improve results. "
                "Consider increasing depth curve gamma."
            )
        else:
            analysis["layer_recommendation"] = (
                "Moderate depth distribution. "
                "2-3 layers recommended for standard quality."
            )
        
        return analysis
    
    def compute_confidence_map(self, depth_a: np.ndarray, 
                                depth_b: np.ndarray) -> np.ndarray:
        """Compute confidence map from two depth estimations.
        
        Areas where two models agree have high confidence.
        Areas of disagreement are flagged for user review.
        
        Args:
            depth_a: First normalized depth map [0, 1]
            depth_b: Second normalized depth map [0, 1]
            
        Returns:
            Confidence map [0, 1] where 1 = high agreement
        """
        # Ensure same size
        if depth_a.shape != depth_b.shape:
            depth_b = cv2.resize(depth_b, (depth_a.shape[1], depth_a.shape[0]),
                                interpolation=cv2.INTER_LINEAR)
        
        # Absolute difference
        diff = np.abs(depth_a - depth_b)
        
        # Convert to confidence (1 = perfect agreement)
        confidence = 1.0 - np.clip(diff * 3.0, 0.0, 1.0)  # Scale: 0.33 diff = 0 confidence
        
        # Smooth confidence map
        confidence = cv2.GaussianBlur(confidence, (15, 15), 0)
        
        return confidence
    
    def get_low_confidence_mask(self, confidence: np.ndarray,
                                 threshold: float = 0.5) -> np.ndarray:
        """Get binary mask of low-confidence regions.
        
        Args:
            confidence: Confidence map [0, 1]
            threshold: Confidence threshold
            
        Returns:
            Binary mask (uint8) where 255 = low confidence
        """
        return (confidence < threshold).astype(np.uint8) * 255
