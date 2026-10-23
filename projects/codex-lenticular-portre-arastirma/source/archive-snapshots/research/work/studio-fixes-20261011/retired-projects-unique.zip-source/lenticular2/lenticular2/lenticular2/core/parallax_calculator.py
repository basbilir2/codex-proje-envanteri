"""Central parallax and optical calculation engine for Lenticular 2.

Orchestrates lens optics, view count feasibility, camera positioning,
parallax budgets, and mathematically correct zero-parallax disparity mapping.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import numpy as np

from lenticular2.utils.math_utils import (
    LensProfile, PrinterProfile, PrintJob,
    get_effective_lpi, get_effective_focal_length, get_lens_pitch_mm,
    get_viewing_angle, is_focal_length_estimated,
    analyze_view_count, recommend_view_counts, ViewCountAnalysis,
    compute_camera_positions, compute_camera_baseline, compute_camera_steps,
    compute_max_parallax_pixels, compute_effective_parallax,
    compute_perceptual_depth_mm, parse_effect_strength, EFFECT_STRENGTH_MAP,
    resolve_zpp_depth, compute_disparity_map_relative, compute_view_shifts,
    compute_output_dimensions,
)

logger = logging.getLogger(__name__)


@dataclass
class ParallaxPlan:
    """Complete parallax computation plan for a print job."""
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
    """Orchestrates all optical and parallax calculations for Lenticular 2."""
    
    def __init__(self, job: PrintJob):
        self.job = job
        self.lens = job.lens_profile
        self.printer = job.printer_profile
        self._plan: Optional[ParallaxPlan] = None
    
    def compute_plan(self) -> ParallaxPlan:
        """Compute the complete physical parallax plan."""
        warnings: List[str] = []
        info: List[str] = []
        
        # 1. Lens Optics
        eff_lpi = get_effective_lpi(self.lens, self.job.viewing_distance_mm)
        eff_focal = get_effective_focal_length(self.lens)
        focal_estimated = is_focal_length_estimated(self.lens)
        viewing_angle = get_viewing_angle(self.lens)
        pitch_mm = get_lens_pitch_mm(self.lens)
        
        if focal_estimated:
            warnings.append(
                "Focal length uses thickness approximation. Pitch test recommended."
            )
        
        if self.lens.calibrated_lpi is None:
            warnings.append(
                f"Using nominal LPI ({self.lens.nominal_lpi}). Computed optical LPI: {eff_lpi:.2f}. "
                "Pitch test strongly recommended for final production."
            )
        
        info.append(f"Effective Optical LPI: {eff_lpi:.2f}")
        info.append(f"Lens Pitch: {pitch_mm:.4f} mm")
        info.append(f"Viewing Angle: {viewing_angle:.1f} deg")
        info.append(f"Focal Length: {eff_focal:.2f} mm" + (" (estimated)" if focal_estimated else ""))
        
        # 2. View Count Selection (Unified with math_utils)
        all_analyses = recommend_view_counts(
            eff_lpi, self.printer.output_raster_ppi,
            self.printer.measured_effective_dpi
        )
        
        if self.job.view_count is not None and self.job.view_count > 0:
            n_views = self.job.view_count
            view_analysis = analyze_view_count(
                n_views, eff_lpi, self.printer.output_raster_ppi,
                self.printer.measured_effective_dpi
            )
            if view_analysis.feasibility == "insufficient":
                warnings.append(f"Requested {n_views} views is physically insufficient: {view_analysis.notes}")
            elif view_analysis.feasibility == "marginal":
                warnings.append(f"Requested {n_views} views is marginal: {view_analysis.notes}")
        else:
            safe_options = [a for a in all_analyses if a.feasibility == "safe"]
            if safe_options:
                view_analysis = safe_options[0]
                n_views = safe_options[0].n_views
            else:
                marginal_options = [a for a in all_analyses if a.feasibility == "marginal"]
                if marginal_options:
                    view_analysis = marginal_options[0]
                    n_views = marginal_options[0].n_views
                    warnings.append(f"No fully safe view count at {eff_lpi:.1f} LPI. Selected best marginal: {n_views}")
                else:
                    n_views = 4
                    view_analysis = analyze_view_count(
                        4, eff_lpi, self.printer.output_raster_ppi,
                        self.printer.measured_effective_dpi
                    )
                    warnings.append(f"Low resolution: using minimum 4 views.")
        
        info.append(f"Selected Views: {n_views} ({view_analysis.feasibility})")
        info.append(f"Raster width per view: {view_analysis.raster_width_per_view:.2f} px")
        
        # 3. Virtual Camera Positioning
        camera_pos = compute_camera_positions(self.lens, n_views, self.job.viewing_distance_mm)
        baseline = compute_camera_baseline(self.lens, n_views, self.job.viewing_distance_mm)
        steps = compute_camera_steps(self.lens, n_views, self.job.viewing_distance_mm)
        
        info.append(f"Total Camera Baseline: {baseline:.2f} mm")
        info.append(f"Avg Camera Step: {steps.mean():.3f} mm")
        
        # 4. Parallax Budgeting
        max_parallax = compute_max_parallax_pixels(eff_lpi, self.printer.output_raster_ppi)
        eff_parallax = compute_effective_parallax(eff_lpi, self.printer.output_raster_ppi, self.job.effect_strength)
        parallax_mm = eff_parallax * 25.4 / self.printer.output_raster_ppi
        perceptual_depth = compute_perceptual_depth_mm(parallax_mm, self.job.viewing_distance_mm)
        strength_factor = parse_effect_strength(self.job.effect_strength)
        
        if strength_factor >= 0.90:
            warnings.append("Extreme parallax budget (>=90%) may cause visible ghosting/crosstalk.")
        
        info.append(f"Parallax Budget: {eff_parallax:.1f} px ({strength_factor*100:.0f}% of {max_parallax:.1f} px max)")
        info.append(f"Estimated 3D Perceptual Depth: ~{perceptual_depth:.1f} mm at {self.job.viewing_distance_mm:.0f} mm viewing")
        
        # 5. Output Pixel Dimensions
        out_w, out_h = compute_output_dimensions(
            self.job.print_width_mm, self.job.print_height_mm,
            self.printer.output_raster_ppi, self.job.bleed_mm
        )
        info.append(f"Output Pixel Dimensions: {out_w} x {out_h} px (Bleed: {self.job.bleed_mm} mm)")
        
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
            effect_strength=str(self.job.effect_strength),
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
        if self._plan is None:
            self.compute_plan()
        return self._plan
    
    def get_zpp_from_selection(self, depth_normalized: np.ndarray,
                               selection_mask: Optional[np.ndarray] = None,
                               mode: Optional[str] = None,
                               offset: Optional[float] = None) -> float:
        """Determine zero-parallax depth from subject selection or center area.
        
        Correctly implements:
        - 'surface': ZPP matches subject depth.
        - 'front' (pop-out): ZPP sits behind subject -> subject pops out!
        - 'behind' (recede): ZPP sits in front of subject -> subject recedes!
        """
        active_mode = mode if mode is not None else self.job.zpp_mode
        active_offset = offset if offset is not None else self.job.zpp_offset
        return resolve_zpp_depth(
            depth_map=depth_normalized,
            selection_mask=selection_mask,
            mode=active_mode,
            offset=active_offset,
            default_zpp=self.job.zpp_depth_value
        )
    
    def compute_disparity(self, depth_normalized: np.ndarray,
                          zpp_depth: Optional[float] = None,
                          selection_mask: Optional[np.ndarray] = None) -> np.ndarray:
        """Compute disparity map from normalized depth.
        
        Correctly links job.zpp_mode and job.zpp_offset when zpp_depth is not directly given.
        """
        plan = self.plan
        if zpp_depth is not None:
            zpp = float(zpp_depth)
        elif selection_mask is not None or self.job.zpp_mode != "surface":
            zpp = self.get_zpp_from_selection(
                depth_normalized, selection_mask, self.job.zpp_mode, self.job.zpp_offset
            )
        else:
            zpp = float(self.job.zpp_depth_value)
        
        return compute_disparity_map_relative(
            depth_normalized=depth_normalized,
            zpp_depth=zpp,
            parallax_budget=plan.effective_parallax_px,
            front_ratio=self.job.front_parallax_ratio,
            curve_fn=self.job.depth_curve,
            gamma=self.job.depth_gamma,
        )
    
    def compute_shifts(self, disparity: np.ndarray) -> List[np.ndarray]:
        """Compute per-view pixel shifts from disparity map."""
        return compute_view_shifts(disparity, self.plan.n_views)
    
    def format_summary(self) -> str:
        """Format a human-readable diagnostic summary."""
        plan = self.plan
        lines = []
        lines.append("=" * 65)
        lines.append("       LENTICULAR 2 - PRECISION OPTICAL PRODUCTION PLAN")
        lines.append("=" * 65)
        lines.append(f"\n[Lens: {self.lens.name}]")
        for item in plan.info:
            lines.append(f"  * {item}")
        
        if plan.warnings:
            lines.append("\n[Warnings / Recommendations]")
            for w in plan.warnings:
                lines.append(f"  [WARN] {w}")
        
        lines.append("\n[Candidate View Allocation]")
        for a in plan.all_view_analyses[:10]:
            marker = "==>" if a.n_views == plan.n_views else "   "
            icon = {"safe": "[OK]", "marginal": "[WARN]", "insufficient": "[FAIL]"}[a.feasibility]
            lines.append(f"  {marker} N={a.n_views:2d} views: {a.raster_width_per_view:.2f} px/view  {icon} {a.feasibility}")
        
        lines.append("=" * 65)
        return "\n".join(lines)
    
    def compare_effects(self, depth_normalized: np.ndarray) -> Dict[str, Any]:
        """Compare all effect presets."""
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
                "budget_usage_pct": factor * 100.0,
            }
        return results
