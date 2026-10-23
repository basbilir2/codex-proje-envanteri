"""Intelligent Pre-Production Scene Analyzer for Lenticular 2.

Analyzes image composition, subject silhouettes, negative spaces/gaps,
and edge depth discontinuities to calculate optimal camera angles,
layer separation budgets, and zero-parallax plane (ZPP) anchors before rendering.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple, List
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


@dataclass
class SceneAnalysisReport:
    """Diagnostic report and recommended parameters computed by SceneAnalyzer."""
    subject_box: Tuple[int, int, int, int]  # (x, y, w, h)
    subject_coverage_pct: float
    subject_depth_mean: float
    background_depth_mean: float
    depth_contrast: float
    negative_space_ratio: float
    edge_jump_intensity: float
    silhouette_complexity: float
    scene_complexity_score: float
    recommended_angle_deg: float
    recommended_baseline_factor: float
    recommended_zpp_depth: float
    recommended_zpp_mode: str
    recommended_views: int
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class SceneAnalyzer:
    """Pre-production image and depth analyzer for intelligent parameter deduction."""
    
    def __init__(self, target_lens_lpi: float = 60.0, output_ppi: int = 720):
        self.target_lens_lpi = float(target_lens_lpi)
        self.output_ppi = int(output_ppi)
        
    def analyze(self, image: np.ndarray, depth: np.ndarray,
                subject_hint_mode: str = "auto") -> SceneAnalysisReport:
        """Inspect RGB image and depth map to calculate optimal 3D parameters.
        
        Args:
            image: (H, W, 3) uint8 RGB image
            depth: (H, W) float32 normalized depth map [0.0, 1.0]
            subject_hint_mode: 'auto', 'center', or 'foreground'
            
        Returns:
            SceneAnalysisReport with computed metrics and recommendations.
        """
        H, W = image.shape[:2]
        total_pixels = float(H * W)
        depth = depth.astype(np.float32)
        
        # 1. Subject segmentation / saliency mask
        if subject_hint_mode == "center":
            mask = np.zeros((H, W), dtype=np.uint8)
            mask[H//4:3*H//4, W//4:3*W//4] = 255
        else:
            # High-depth threshold + central bias
            d_thresh = np.percentile(depth, 65)
            high_d = (depth >= d_thresh).astype(np.uint8) * 255
            
            # Distance from center weighting
            y_coords, x_coords = np.ogrid[:H, :W]
            center_dist = np.sqrt(((x_coords - W / 2) / (W / 2)) ** 2 + ((y_coords - H / 2) / (H / 2)) ** 2)
            center_weight = np.clip(1.4 - center_dist, 0.0, 1.0)
            
            candidate = ((high_d > 0) & (center_weight > 0.4)).astype(np.uint8) * 255
            
            # Find largest connected component
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(candidate)
            if num_labels > 1:
                largest_idx = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
                mask = (labels == largest_idx).astype(np.uint8) * 255
            else:
                mask = candidate
                
            if mask.sum() < 0.02 * total_pixels:
                # Fallback to central bounding box
                mask[H//4:3*H//4, W//4:3*W//4] = 255
                
        # Subject bounding box
        coords = cv2.findNonZero(mask)
        if coords is not None:
            bx, by, bw, bh = cv2.boundingRect(coords)
        else:
            bx, by, bw, bh = (W // 4, H // 4, W // 2, H // 2)
            
        subject_coverage = float(mask.sum() / 255.0) / total_pixels
        
        # 2. Depth Statistics
        subject_depth = float(np.median(depth[mask > 0])) if (mask > 0).any() else 0.70
        bg_mask = (mask == 0)
        bg_depth = float(np.median(depth[bg_mask])) if bg_mask.any() else 0.20
        depth_contrast = float(abs(subject_depth - bg_depth))
        
        # 3. Negative Space & Holes
        # Invert subject mask inside bounding box to detect holes/gaps
        sub_roi = mask[by:by+bh, bx:bx+bw]
        contours, hierarchy = cv2.findContours(sub_roi, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        hole_area = 0
        if hierarchy is not None:
            for i, h in enumerate(hierarchy[0]):
                if h[3] != -1:  # Has a parent, meaning it's an internal hole/gap
                    hole_area += cv2.contourArea(contours[i])
        neg_space_ratio = float(hole_area) / max(1.0, float(bw * bh))
        
        # 4. Edge Discontinuity & Silhouette Complexity
        sobel_x = cv2.Sobel(depth, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(depth, cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = np.sqrt(sobel_x ** 2 + sobel_y ** 2)
        edge_jump_intensity = float(np.percentile(grad_mag, 95))
        
        sub_contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        perimeter = sum(cv2.arcLength(c, True) for c in sub_contours)
        area = max(1.0, float(mask.sum() / 255.0))
        # Normalized isoperimetric ratio (circular = 1.0, complex jagged = higher)
        silhouette_complexity = float((perimeter ** 2) / (4.0 * np.pi * area))
        
        # 5. Scene Complexity Score & Angle Derivation
        # High jumps + high complexity -> lower angle to prevent ghosting/tearing
        # Low jumps + smooth shapes -> wider angle permissible
        H_edge = np.clip(edge_jump_intensity * 2.0, 0.0, 1.0)
        J_sil = np.clip((silhouette_complexity - 1.0) / 10.0, 0.0, 1.0)
        
        complexity_score = 1.0 / (1.0 + 3.0 * H_edge + 2.5 * J_sil)
        recommended_angle = float(np.clip(1.40 * complexity_score, 0.65, 1.50))
        baseline_factor = float(recommended_angle / 1.10)
        
        # 6. Recommended ZPP Mode & Value
        # For portraits / clear subjects: place subject at surface (ZPP = subject_depth)
        # For floating emblems / logos: pop-out (front)
        if neg_space_ratio > 0.08:
            rec_zpp_mode = "surface"  # keep complex holes pinned to print surface to minimize blur
            rec_zpp = subject_depth
        else:
            rec_zpp_mode = "front" if subject_depth > 0.65 else "surface"
            rec_zpp = max(0.10, subject_depth - 0.12) if rec_zpp_mode == "front" else subject_depth
            
        # 7. Recommended View Count
        # High edge jump benefits from higher view counts to avoid stepping
        c_raster = self.output_ppi / self.target_lens_lpi
        max_safe_views = int(c_raster / 1.2)
        rec_views = min(16, max(8, (max_safe_views // 2) * 2))
        
        # Diagnostic recommendations & warnings
        recommendations = []
        warnings = []
        
        recommendations.append(f"Subject localized at ({bx}, {by}, {bw}x{bh}), {subject_coverage*100:.1f}% scene coverage.")
        recommendations.append(f"Derived camera angle: +/-{recommended_angle:.2f} deg (Baseline factor: {baseline_factor:.2f}x).")
        recommendations.append(f"Optimal Zero-Parallax Plane: {rec_zpp:.2f} (Mode: '{rec_zpp_mode}').")
        recommendations.append(f"Recommended view count: {rec_views} views at {self.target_lens_lpi} LPI / {self.output_ppi} PPI.")
        
        if edge_jump_intensity > 0.40:
            warnings.append(f"High depth edge gradient ({edge_jump_intensity:.2f}). Use Guided Filter edge refinement to avoid halos.")
        if neg_space_ratio > 0.05:
            recommendations.append(f"Internal negative spaces detected ({neg_space_ratio*100:.1f}%). DIBR hole inpainting enabled.")
        if depth_contrast < 0.20:
            warnings.append("Low depth dynamic range. Consider applying depth stretching curve before rendering.")
            
        return SceneAnalysisReport(
            subject_box=(bx, by, bw, bh),
            subject_coverage_pct=subject_coverage * 100.0,
            subject_depth_mean=subject_depth,
            background_depth_mean=bg_depth,
            depth_contrast=depth_contrast,
            negative_space_ratio=neg_space_ratio,
            edge_jump_intensity=edge_jump_intensity,
            silhouette_complexity=silhouette_complexity,
            scene_complexity_score=complexity_score,
            recommended_angle_deg=recommended_angle,
            recommended_baseline_factor=baseline_factor,
            recommended_zpp_depth=rec_zpp,
            recommended_zpp_mode=rec_zpp_mode,
            recommended_views=rec_views,
            recommendations=recommendations,
            warnings=warnings,
        )
