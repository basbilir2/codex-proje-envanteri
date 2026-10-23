"""End-to-End Production Pipeline for Lenticular 2.

Unifies profile loading, scene analysis, depth optimization,
multi-view DIBR generation, coordinate interlacing, and quality diagnostics.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
import numpy as np

from lenticular2.utils.math_utils import (
    LensProfile, PrinterProfile, PrintJob,
    compute_output_dimensions,
)
from lenticular2.utils.image_utils import (
    load_image, save_image, resize_to_output,
    create_animation_frames, save_animation,
)
from lenticular2.core.parallax_calculator import ParallaxCalculator, ParallaxPlan
from lenticular2.core.depth_optimizer import DepthOptimizer
from lenticular2.core.view_generator_dibr import generate_views_dibr
from lenticular2.core.interlacing import interlace, create_interlacing_preview
from lenticular2.analysis.scene_analyzer import SceneAnalyzer, SceneAnalysisReport

logger = logging.getLogger(__name__)


def load_lens_profiles(config_path: Optional[Union[str, Path]] = None) -> Dict[str, LensProfile]:
    """Load lens profiles from JSON configuration."""
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "config" / "lens_profiles.json"
    else:
        config_path = Path(config_path)
        
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    profiles = {}
    for entry in data.get("profiles", []):
        lp = LensProfile(
            name=entry["name"],
            nominal_lpi=float(entry["nominal_lpi"]),
            calibrated_lpi=float(entry["calibrated_lpi"]) if entry.get("calibrated_lpi") else None,
            thickness_mm=float(entry.get("thickness_mm", 1.0)),
            refractive_index=float(entry.get("refractive_index", 1.57)),
            effective_focal_length_mm=float(entry["effective_focal_length_mm"]) if entry.get("effective_focal_length_mm") else None,
            back_focal_distance_mm=float(entry["back_focal_distance_mm"]) if entry.get("back_focal_distance_mm") else None,
            lens_type=entry.get("lens_type", "3D"),
            orientation=entry.get("orientation", "vertical"),
            substrate_gap_mm=float(entry.get("substrate_gap_mm", 0.0)),
            viewing_angle_measured_deg=float(entry["viewing_angle_measured_deg"]) if entry.get("viewing_angle_measured_deg") else None,
            calibration_data=entry.get("calibration_data", []),
            notes=entry.get("notes", ""),
        )
        profiles[lp.name] = lp
    return profiles


def load_printer_profiles(config_path: Optional[Union[str, Path]] = None) -> Dict[str, PrinterProfile]:
    """Load printer profiles from JSON configuration."""
    if config_path is None:
        config_path = Path(__file__).resolve().parent.parent / "config" / "printer_profiles.json"
    else:
        config_path = Path(config_path)
        
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    profiles = {}
    for entry in data.get("profiles", []):
        pp = PrinterProfile(
            name=entry["name"],
            output_raster_ppi=int(entry["output_raster_ppi"]),
            addressable_dpi_h=int(entry.get("addressable_dpi_h", 1200)),
            addressable_dpi_v=int(entry.get("addressable_dpi_v", 1200)),
            measured_effective_dpi=int(entry["measured_effective_dpi"]) if entry.get("measured_effective_dpi") else None,
            max_print_width_mm=float(entry.get("max_print_width_mm", 600.0)),
            max_print_height_mm=float(entry.get("max_print_height_mm", 400.0)),
            color_mode=entry.get("color_mode", "CMYK"),
            icc_profile_path=entry.get("icc_profile_path"),
            notes=entry.get("notes", ""),
        )
        profiles[pp.name] = pp
    return profiles


class ProductionPipeline:
    """Master production pipeline orchestrating the entire Lenticular 2 process."""
    
    def __init__(self,
                 lens_profile: LensProfile,
                 printer_profile: PrinterProfile,
                 output_dir: Union[str, Path] = "outputs"):
        self.lens = lens_profile
        self.printer = printer_profile
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def run(self,
            image_path: Union[str, Path],
            depth_path: Union[str, Path],
            print_width_mm: float = 150.0,
            print_height_mm: float = 100.0,
            viewing_distance_mm: float = 400.0,
            effect_strength: str = "balanced",
            zpp_mode: str = "surface",
            view_count: Optional[int] = None,
            registration_offset_mm: float = 0.0,
            skew_degrees: float = 0.0,
            job_name: str = "lenticular_print") -> Dict[str, Any]:
        """Execute end-to-end lenticular preparation and production."""
        
        logger.info(f"Starting Lenticular 2 Production Pipeline: {job_name}")
        job_dir = self.output_dir / job_name
        job_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Load Image and Depth safely
        rgb_raw = load_image(image_path, mode="rgb")
        depth_raw = load_image(depth_path, mode="gray")
        
        # 2. Pre-production Scene Analysis
        analyzer = SceneAnalyzer(target_lens_lpi=self.lens.nominal_lpi, output_ppi=self.printer.output_raster_ppi)
        # Temporary normalize for analysis
        temp_depth = depth_raw.astype(np.float32) / 255.0 if depth_raw.dtype == np.uint8 else depth_raw.astype(np.float32)
        analysis_report = analyzer.analyze(rgb_raw, temp_depth)
        
        # 3. Create PrintJob specification
        job = PrintJob(
            lens_profile=self.lens,
            printer_profile=self.printer,
            print_width_mm=print_width_mm,
            print_height_mm=print_height_mm,
            viewing_distance_mm=viewing_distance_mm,
            effect_strength=effect_strength,
            zpp_mode=zpp_mode,
            view_count=view_count,
            registration_offset_mm=registration_offset_mm,
            skew_degrees=skew_degrees,
            use_subpixel_interlacing=False,  # CMYK UV flatbed standard
        )
        
        # 4. Parallax Plan Calculation
        calculator = ParallaxCalculator(job)
        plan = calculator.plan
        
        # 5. Resize inputs to exact print dimensions
        target_w, target_h = plan.output_width_px, plan.output_height_px
        rgb_resized = resize_to_output(rgb_raw, target_w, target_h)
        depth_resized = resize_to_output(depth_raw, target_w, target_h)
        
        # 6. Float32 Depth Optimization (no 8-bit quantization)
        optimizer = DepthOptimizer()
        depth_optimized = optimizer.optimize(
            depth_resized,
            rgb_guide=rgb_resized,
            denoise=True,
            edge_refine=True,
            apply_curve=False,  # Let disparity calculator handle curve to prevent double gamma
        )
        
        # 7. Compute Correct Disparity Map
        disparity_map = calculator.compute_disparity(depth_optimized)
        
        # 8. Multi-View Rendering via Vectorized DIBR
        views = generate_views_dibr(rgb_resized, disparity_map, plan.n_views, fill_holes=True)
        
        # 9. Coordinate Interlacing with true normal projection
        interlaced = interlace(views, job)
        
        # 10. Save Deliverables
        interlaced_path = job_dir / f"{job_name}_interlaced.tif"
        save_image(interlaced, interlaced_path, ppi=self.printer.output_raster_ppi)
        
        preview_anim_path = job_dir / f"{job_name}_lookaround.gif"
        frames = create_animation_frames(views)
        save_animation(frames, preview_anim_path, fps=12)
        
        depth_opt_path = job_dir / f"{job_name}_depth_opt.png"
        save_image((depth_optimized * 255.0).astype(np.uint8), depth_opt_path)
        
        report_data = {
            "job_name": job_name,
            "lens": self.lens.name,
            "nominal_lpi": self.lens.nominal_lpi,
            "effective_lpi": plan.effective_lpi,
            "printer": self.printer.name,
            "output_ppi": self.printer.output_raster_ppi,
            "print_size_mm": [print_width_mm, print_height_mm],
            "output_size_px": [target_w, target_h],
            "n_views": plan.n_views,
            "camera_baseline_mm": plan.camera_baseline_mm,
            "effective_parallax_px": plan.effective_parallax_px,
            "perceptual_depth_mm": plan.perceptual_depth_mm,
            "zpp_mode": zpp_mode,
            "effect_strength": effect_strength,
            "registration_offset_mm": registration_offset_mm,
            "skew_degrees": skew_degrees,
            "analysis_recommendations": analysis_report.recommendations,
            "warnings": plan.warnings + analysis_report.warnings,
        }
        
        report_path = job_dir / f"{job_name}_production_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Pipeline complete! Artifacts saved to: {job_dir}")
        return {
            "interlaced_path": str(interlaced_path),
            "preview_animation_path": str(preview_anim_path),
            "report_path": str(report_path),
            "plan_summary": calculator.format_summary(),
            "report_data": report_data,
        }
