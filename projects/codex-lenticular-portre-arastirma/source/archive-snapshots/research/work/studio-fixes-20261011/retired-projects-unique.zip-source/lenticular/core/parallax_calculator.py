"""Central parallax and optical calculation engine.

Orchestrates lens optics, view count analysis, camera positions,
parallax budgets, and disparity computation for a complete print job.
"""

import logging
import math
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

import numpy as np

from utils.math_utils import (
    LensProfile, PrinterProfile, PrintJob,
    get_effective_lpi, get_effective_focal_length, get_lens_pitch_mm,
    get_viewing_angle, is_focal_length_estimated,
    analyze_view_count, recommend_view_counts, ViewCountAnalysis,
    compute_camera_positions, compute_camera_baseline, compute_camera_steps,
    compute_max_parallax_pixels, compute_effective_parallax,
    compute_perceptual_depth_mm, EFFECT_STRENGTH_MAP,
    compute_disparity_map_relative, compute_disparity_map_metric,
    compute_view_shifts, compute_output_dimensions,
    compute_print_job_summary,
)

logger = logging.getLogger(__name__)


@dataclass
class ParallaxPlan:
    """Complete parallax computation plan for a print job.
    
    Contains all derived parameters needed for multi-view generation.
    """
    # Lens optics
    effective_lpi: float
    effective_focal_length_mm: float
    focal_length_estimated: bool
    viewing_angle_deg: float
    lens_pitch_mm: float
    
    # Views
    n_views: int
    view_analysis: ViewCountAnalysis
    all_view_analyses: List[ViewCountAnalysis]
    
    # Camera
    camera_positions_mm: np.ndarray  # shape (n_views,)
    camera_baseline_mm: float
    camera_steps_mm: np.ndarray  # shape (n_views-1,)
    
    # Parallax
    max_parallax_px: float
    effective_parallax_px: float
    parallax_mm: float
    perceptual_depth_mm: float
    effect_strength: str
    strength_factor: float
    front_parallax_ratio: float
    
    # Output
    output_width_px: int
    output_height_px: int
    
    # Warnings and info
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)


class ParallaxCalculator:
    """Orchestrates all optical and parallax calculations."""
    
    def __init__(self, job: PrintJob):
        """Initialize with a print job specification.
        
        Args:
            job: Complete print job specification
        """
        self.job = job
        self.lens = job.lens_profile
        self.printer = job.printer_profile
        self._plan: Optional[ParallaxPlan] = None
    
    def compute_plan(self) -> ParallaxPlan:
        """Compute the complete parallax plan.
        
        Returns:
            ParallaxPlan with all derived parameters
        """
        warnings = []
        info = []
        
        # --- Lens Optics ---
        eff_lpi = get_effective_lpi(self.lens, self.job.viewing_distance_mm)
        eff_focal = get_effective_focal_length(self.lens)
        focal_estimated = is_focal_length_estimated(self.lens)
        viewing_angle = get_viewing_angle(self.lens)
        pitch_mm = get_lens_pitch_mm(self.lens)
        
        if focal_estimated:
            warnings.append(
                "Focal length uses thin-lens approximation (f ≈ thickness). "
                "Results may be inaccurate. Pitch test and viewing test recommended."
            )
        
        if self.lens.calibrated_lpi is None:
            warnings.append(
                f"Using nominal LPI ({self.lens.nominal_lpi}). "
                f"Computed optical LPI: {eff_lpi:.2f}. "
                f"Pitch calibration strongly recommended for accurate interlacing."
            )
        
        info.append(f"Effective LPI: {eff_lpi:.2f}")
        info.append(f"Lens pitch: {pitch_mm:.4f} mm")
        info.append(f"Viewing angle: {viewing_angle:.1f}°")
        info.append(f"Effective focal length: {eff_focal:.2f} mm"
                    + (" (estimated)" if focal_estimated else ""))
        
        # --- View Count ---
        all_analyses = recommend_view_counts(
            eff_lpi, self.printer.output_raster_ppi,
            self.printer.measured_effective_dpi
        )
        
        if self.job.view_count is not None:
            n_views = self.job.view_count
            view_analysis = analyze_view_count(
                n_views, eff_lpi, self.printer.output_raster_ppi,
                self.printer.measured_effective_dpi
            )
            if view_analysis.feasibility == "insufficient":
                warnings.append(
                    f"Requested {n_views} views exceeds physical limits: "
                    f"{view_analysis.notes}"
                )
            elif view_analysis.feasibility == "marginal":
                warnings.append(
                    f"Requested {n_views} views is marginal: {view_analysis.notes}"
                )
        else:
            # Auto-select: highest safe view count
            safe = [a for a in all_analyses if a.feasibility == "safe"]
            if safe:
                n_views = safe[0].n_views
                view_analysis = safe[0]
            else:
                # Fallback: best marginal
                marginal = [a for a in all_analyses if a.feasibility == "marginal"]
                if marginal:
                    n_views = marginal[0].n_views
                    view_analysis = marginal[0]
                    warnings.append(f"No fully safe view count found. Using marginal: {n_views}")
                else:
                    n_views = 4  # absolute minimum
                    view_analysis = analyze_view_count(
                        4, eff_lpi, self.printer.output_raster_ppi,
                        self.printer.measured_effective_dpi
                    )
                    warnings.append("Resolution too low for lenticular. Using minimum 4 views.")
        
        info.append(f"View count: {n_views} ({view_analysis.feasibility})")
        info.append(f"Raster samples/lenticule: {view_analysis.raster_samples_per_lenticule:.2f}")
        info.append(f"Raster px/view: {view_analysis.raster_width_per_view:.2f}")
        
        # --- Camera Positions ---
        camera_pos = compute_camera_positions(
            self.lens, n_views, self.job.viewing_distance_mm
        )
        baseline = compute_camera_baseline(
            self.lens, n_views, self.job.viewing_distance_mm
        )
        steps = compute_camera_steps(
            self.lens, n_views, self.job.viewing_distance_mm
        )
        
        info.append(f"Camera baseline: {baseline:.2f} mm")
        info.append(f"Camera step (avg): {steps.mean():.3f} mm")
        
        # --- Parallax Budget ---
        max_parallax = compute_max_parallax_pixels(eff_lpi, self.printer.output_raster_ppi)
        eff_parallax = compute_effective_parallax(
            eff_lpi, self.printer.output_raster_ppi, self.job.effect_strength
        )
        parallax_mm = eff_parallax * 25.4 / self.printer.output_raster_ppi
        perceptual_depth = compute_perceptual_depth_mm(
            parallax_mm, self.job.viewing_distance_mm
        )
        strength_factor = EFFECT_STRENGTH_MAP.get(self.job.effect_strength, 0.55)
        
        if self.job.effect_strength == "extreme":
            warnings.append(
                "Extreme parallax (95% budget) may cause visible ghosting. "
                "Small test print strongly recommended before final production."
            )
        
        info.append(f"Parallax budget: {eff_parallax:.1f} px "
                    f"({strength_factor*100:.0f}% of {max_parallax:.1f} px max)")
        info.append(f"Parallax on print: ±{parallax_mm/2:.2f} mm")
        info.append(f"Estimated perceptual depth: ~{perceptual_depth:.1f} mm "
                    f"at {self.job.viewing_distance_mm:.0f} mm viewing distance")
        
        # --- Output Dimensions ---
        out_w, out_h = compute_output_dimensions(
            self.job.print_width_mm, self.job.print_height_mm,
            self.printer.output_raster_ppi
        )
        
        info.append(f"Output dimensions: {out_w} × {out_h} px")
        
        # --- Build Plan ---
        self._plan = ParallaxPlan(
            effective_lpi=eff_lpi,
            effective_focal_length_mm=eff_focal,
            focal_length_estimated=focal_estimated,
            viewing_angle_deg=viewing_angle,
            lens_pitch_mm=pitch_mm,
            n_views=n_views,
            view_analysis=view_analysis,
            all_view_analyses=all_analyses,
            camera_positions_mm=camera_pos,
            camera_baseline_mm=baseline,
            camera_steps_mm=steps,
            max_parallax_px=max_parallax,
            effective_parallax_px=eff_parallax,
            parallax_mm=parallax_mm,
            perceptual_depth_mm=perceptual_depth,
            effect_strength=self.job.effect_strength,
            strength_factor=strength_factor,
            front_parallax_ratio=self.job.front_parallax_ratio,
            output_width_px=out_w,
            output_height_px=out_h,
            warnings=warnings,
            info=info,
        )
        
        return self._plan
    
    @property
    def plan(self) -> ParallaxPlan:
        """Get or compute the parallax plan."""
        if self._plan is None:
            self.compute_plan()
        return self._plan
    
    def compute_disparity(self, depth_normalized: np.ndarray,
                          zpp_depth: Optional[float] = None) -> np.ndarray:
        """Compute disparity map from normalized depth.
        
        Args:
            depth_normalized: Normalized depth map [0, 1], white=near
            zpp_depth: Zero-parallax plane depth value.
                       If None, uses job.zpp_depth_value
                       
        Returns:
            Disparity map in pixels
        """
        plan = self.plan
        zpp = zpp_depth if zpp_depth is not None else self.job.zpp_depth_value
        
        return compute_disparity_map_relative(
            depth_normalized=depth_normalized,
            zpp_depth=zpp,
            parallax_budget=plan.effective_parallax_px,
            front_ratio=self.job.front_parallax_ratio,
            curve_fn=self.job.depth_curve,
            gamma=self.job.depth_gamma,
        )
    
    def compute_shifts(self, disparity: np.ndarray) -> List[np.ndarray]:
        """Compute per-view pixel shifts from disparity map.
        
        Args:
            disparity: Disparity map in pixels
            
        Returns:
            List of shift maps, one per view
        """
        return compute_view_shifts(disparity, self.plan.n_views)
    
    def get_zpp_from_selection(self, depth_normalized: np.ndarray,
                               selection_mask: np.ndarray,
                               mode: str = "surface") -> float:
        """Determine zero-parallax depth from user's object selection.
        
        Args:
            depth_normalized: Normalized depth map [0, 1]
            selection_mask: Binary mask of selected region
            mode: 'surface' (object on print surface),
                  'front' (object pops out),
                  'behind' (object recedes)
                  
        Returns:
            Zero-parallax plane depth value
        """
        # Get average depth of selected region
        selected_depths = depth_normalized[selection_mask > 0]
        if len(selected_depths) == 0:
            logger.warning("Empty selection, using center region")
            h, w = depth_normalized.shape[:2]
            selected_depths = depth_normalized[h//3:2*h//3, w//3:2*w//3].flatten()
        
        subject_depth = float(np.median(selected_depths))
        
        if mode == "surface":
            return subject_depth
        elif mode == "front":
            # Shift ZPP behind subject so subject pops out
            offset = 0.15  # Adjustable
            return min(subject_depth + offset, 0.95)
        elif mode == "behind":
            # Shift ZPP in front of subject so subject recedes
            offset = 0.15
            return max(subject_depth - offset, 0.05)
        else:
            return subject_depth
    
    def format_summary(self) -> str:
        """Format a human-readable summary of the parallax plan."""
        plan = self.plan
        lines = []
        lines.append("=" * 60)
        lines.append("LENTICULAR PRINT — PARALLAX PLAN")
        lines.append("=" * 60)
        
        lines.append(f"\n--- Lens: {self.lens.name} ---")
        for item in plan.info:
            lines.append(f"  {item}")
        
        if plan.warnings:
            lines.append(f"\n--- Warnings ---")
            for w in plan.warnings:
                lines.append(f"  ⚠ {w}")
        
        lines.append(f"\n--- View Count Options ---")
        for a in plan.all_view_analyses[:8]:
            marker = "→" if a.n_views == plan.n_views else " "
            icon = {"safe": "✅", "marginal": "⚠️", "insufficient": "❌"}[a.feasibility]
            lines.append(
                f"  {marker} N={a.n_views:3d}: "
                f"{a.raster_width_per_view:.2f} px/view "
                f"{icon} {a.feasibility}"
            )
        
        lines.append("\n" + "=" * 60)
        return "\n".join(lines)
    
    def compare_effects(self, depth_normalized: np.ndarray) -> dict:
        """Generate comparison data for different effect strengths.
        
        Args:
            depth_normalized: Normalized depth map
            
        Returns:
            Dict mapping effect name to parallax info
        """
        plan = self.plan
        results = {}
        
        for name, factor in EFFECT_STRENGTH_MAP.items():
            eff_px = plan.max_parallax_px * factor
            eff_mm = eff_px * 25.4 / self.printer.output_raster_ppi
            depth_mm = compute_perceptual_depth_mm(eff_mm, self.job.viewing_distance_mm)
            
            results[name] = {
                "strength_factor": factor,
                "parallax_px": eff_px,
                "parallax_mm": eff_mm,
                "perceptual_depth_mm": depth_mm,
                "budget_usage_pct": factor * 100,
            }
        
        return results
