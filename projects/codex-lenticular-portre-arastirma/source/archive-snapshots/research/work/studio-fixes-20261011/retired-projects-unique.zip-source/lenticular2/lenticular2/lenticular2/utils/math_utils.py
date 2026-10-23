"""Mathematical utilities for lenticular lens optics and print calculations.

Lenticular 2 Engine - Rigorously corrected and physically verified optics.

All physical units:
- Distances: mm (millimeters) unless noted otherwise
- Angles: degrees (converted internally to radians as needed)
- Resolution: PPI / DPI / LPI
- Pixels: integer or float pixel counts
"""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any


@dataclass
class LensProfile:
    """Physical and optical properties of a lenticular lens sheet."""
    name: str
    nominal_lpi: float  # Manufacturer's stated LPI
    calibrated_lpi: Optional[float] = None  # Measured optical LPI from pitch test
    thickness_mm: float = 1.0
    refractive_index: float = 1.57  # Acrylic/PETG typically 1.52 - 1.60
    effective_focal_length_mm: Optional[float] = None
    back_focal_distance_mm: Optional[float] = None
    lens_type: str = "3D"  # "3D", "Flip", "Morph"
    orientation: str = "vertical"  # "vertical" or "horizontal"
    substrate_gap_mm: float = 0.0  # Gap between lens and print surface
    viewing_angle_measured_deg: Optional[float] = None
    calibration_data: List[dict] = field(default_factory=list)
    # calibration_data entries: {"distance_mm": float, "measured_lpi": float}
    notes: str = ""


@dataclass
class PrinterProfile:
    """Printer resolution and capability profile."""
    name: str
    output_raster_ppi: int  # Output file pixel density (e.g. 720, 1440)
    addressable_dpi_h: int = 1200  # Print head horizontal DPI
    addressable_dpi_v: int = 1200  # Print head vertical DPI
    measured_effective_dpi: Optional[int] = None  # After RIP, dot gain, etc.
    max_print_width_mm: float = 600.0
    max_print_height_mm: float = 400.0
    color_mode: str = "CMYK"  # "CMYK" or "RGB"
    icc_profile_path: Optional[str] = None
    notes: str = ""


@dataclass
class PrintJob:
    """Complete print job specification for Lenticular 2."""
    lens_profile: LensProfile
    printer_profile: PrinterProfile
    print_width_mm: float
    print_height_mm: float
    viewing_distance_mm: float = 400.0
    print_direction: str = "horizontal"  # Parallax direction ("horizontal" or "vertical")
    effect_strength: str = "balanced"  # "natural", "balanced", "strong", "extreme" or numeric float
    zpp_depth_value: float = 0.5  # Zero-parallax plane in normalized depth [0,1]
    zpp_mode: str = "surface"  # "front", "surface", "behind"
    zpp_offset: float = 0.15  # Offset applied when zpp_mode is 'front' or 'behind'
    view_count: Optional[int] = None  # None = auto-calculate
    use_subpixel_interlacing: bool = False  # False = whole pixel (correct for CMYK UV Flatbeds)
    registration_offset_mm: float = 0.0  # Measured phase alignment shift in mm
    skew_degrees: float = 0.0  # Measured angular tilt / rotation in degrees
    flip_views: bool = False  # Reverse view rendering order (L/R inversion)
    depth_curve: str = "linear"  # "linear", "gamma", "sigmoid"
    depth_gamma: float = 1.0  # Used when depth_curve="gamma"
    front_parallax_ratio: float = 0.4  # Budget split: 40% front (pop-out), 60% back
    bleed_mm: float = 0.0  # Bleed margin around image in mm


# ============================================================
# Lens Optics
# ============================================================

def get_effective_lpi(lens: LensProfile, viewing_distance_mm: Optional[float] = None) -> float:
    """Get the effective (optical) LPI for interlacing.
    
    Priority:
    1. Calibrated LPI from pitch test (measured ground truth)
    2. Distance-interpolated calibration data if available
    3. Theoretical optical LPI accounting for distance, thickness, and refractive index n:
       LPI_eff = LPI_nom * (D / (D - (t / n)))
    4. Fallback to nominal LPI
    """
    # 1. Direct calibrated value
    if lens.calibrated_lpi is not None and lens.calibrated_lpi > 0:
        return float(lens.calibrated_lpi)
    
    # 2. Distance-specific calibration table
    if viewing_distance_mm is not None and lens.calibration_data:
        # If multiple points, do linear interpolation or nearest
        if len(lens.calibration_data) == 1:
            return float(lens.calibration_data[0]["measured_lpi"])
        points = sorted(lens.calibration_data, key=lambda c: c["distance_mm"])
        dists = [p["distance_mm"] for p in points]
        lpis = [p["measured_lpi"] for p in points]
        if viewing_distance_mm <= dists[0]:
            return float(lpis[0])
        if viewing_distance_mm >= dists[-1]:
            return float(lpis[-1])
        return float(np.interp(viewing_distance_mm, dists, lpis))
    
    # 3. Theoretical correction with dielectric Snell thickness (t / n)
    if viewing_distance_mm is not None and lens.thickness_mm > 0:
        d = float(viewing_distance_mm)
        t = float(lens.thickness_mm)
        n = float(lens.refractive_index) if lens.refractive_index and lens.refractive_index > 1.0 else 1.57
        optical_thickness = t / n
        if d > optical_thickness:
            return float(lens.nominal_lpi * (d / (d - optical_thickness)))
    
    # 4. Fallback nominal
    return float(lens.nominal_lpi)


def get_effective_focal_length(lens: LensProfile) -> float:
    """Determine effective focal length using available optical data.
    
    Priority:
    1. Direct effective_focal_length_mm
    2. Back focal distance
    3. Derived from measured viewing angle: f = (p/2) / tan(alpha/2)
    4. Dielectric thickness approximation: f ≈ thickness / n (or thickness if n not set)
    """
    if lens.effective_focal_length_mm is not None and lens.effective_focal_length_mm > 0:
        return float(lens.effective_focal_length_mm)
    
    if lens.back_focal_distance_mm is not None and lens.back_focal_distance_mm > 0:
        return float(lens.back_focal_distance_mm)
    
    if lens.viewing_angle_measured_deg is not None and lens.viewing_angle_measured_deg > 0:
        p = get_lens_pitch_mm(lens)
        half_angle_rad = math.radians(lens.viewing_angle_measured_deg / 2.0)
        if half_angle_rad > 0:
            return float((p / 2.0) / math.tan(half_angle_rad))
    
    n = float(lens.refractive_index) if lens.refractive_index and lens.refractive_index > 1.0 else 1.57
    return float(lens.thickness_mm / n) if n > 0 else float(lens.thickness_mm)


def get_lens_pitch_mm(lens: LensProfile) -> float:
    """Get the physical pitch width of one lenticule in millimeters."""
    lpi = lens.calibrated_lpi if lens.calibrated_lpi else lens.nominal_lpi
    return 25.4 / float(lpi)


def get_viewing_angle(lens: LensProfile) -> float:
    """Calculate the total optical viewing angle of the lens in degrees."""
    if lens.viewing_angle_measured_deg is not None and lens.viewing_angle_measured_deg > 0:
        return float(lens.viewing_angle_measured_deg)
    
    p = get_lens_pitch_mm(lens)
    f = get_effective_focal_length(lens)
    return float(2.0 * math.degrees(math.atan(p / (2.0 * f))))


def is_focal_length_estimated(lens: LensProfile) -> bool:
    """Check if focal length is using thickness approximation."""
    return (lens.effective_focal_length_mm is None and
            lens.back_focal_distance_mm is None and
            lens.viewing_angle_measured_deg is None)


# ============================================================
# View Count Analysis (Even and Odd Support)
# ============================================================

@dataclass
class ViewCountAnalysis:
    """Analysis result for a candidate view count."""
    n_views: int
    raster_samples_per_lenticule: float  # C_raster = PPI / LPI
    printer_dots_per_lenticule: float  # C_printer = DPI / LPI
    raster_width_per_view: float  # w_raster / view
    printer_width_per_view: Optional[float]  # w_printer / view
    feasibility: str  # "safe", "marginal", "insufficient"
    notes: str


def analyze_view_count(n_views: int, effective_lpi: float,
                       output_ppi: int,
                       effective_dpi: Optional[int] = None) -> ViewCountAnalysis:
    """Analyze physical feasibility of a candidate view count."""
    if n_views <= 0 or effective_lpi <= 0 or output_ppi <= 0:
        raise ValueError(f"Invalid parameters: n_views={n_views}, lpi={effective_lpi}, ppi={output_ppi}")
    
    c_raster = float(output_ppi) / float(effective_lpi)
    w_raster = c_raster / float(n_views)
    
    c_printer = None
    w_printer = None
    if effective_dpi is not None and effective_dpi > 0:
        c_printer = float(effective_dpi) / float(effective_lpi)
        w_printer = c_printer / float(n_views)
    
    if w_raster < 1.0:
        feasibility = "insufficient"
        notes = f"Raster width per view ({w_raster:.2f} px) < 1.0. Insufficient file resolution."
    elif w_printer is not None and w_printer < 1.5:
        feasibility = "marginal"
        notes = f"Printer dots per view ({w_printer:.2f} dots) < 1.5. Dot-gain / optical blur likely."
    elif w_raster < 1.2:
        feasibility = "marginal"
        notes = f"Raster width per view ({w_raster:.2f} px) is borderline (< 1.2 px)."
    else:
        feasibility = "safe"
        notes = f"Adequate resolution: {w_raster:.2f} raster px/view"
        if w_printer:
            notes += f", {w_printer:.2f} printer dots/view"
    
    return ViewCountAnalysis(
        n_views=n_views,
        raster_samples_per_lenticule=c_raster,
        printer_dots_per_lenticule=c_printer if c_printer else 0.0,
        raster_width_per_view=w_raster,
        printer_width_per_view=w_printer,
        feasibility=feasibility,
        notes=notes
    )


def recommend_view_counts(effective_lpi: float, output_ppi: int,
                          effective_dpi: Optional[int] = None,
                          min_views: int = 4,
                          max_views: int = 36,
                          allow_odd: bool = True) -> List[ViewCountAnalysis]:
    """Analyze all candidate view counts and return ranked recommendations.
    
    Supports both even and odd view counts. Odd view counts are valuable
    because the center view (index (N-1)/2) points straight at 0 degrees.
    """
    max_theoretical = int(output_ppi / effective_lpi)
    actual_max = min(max_views, max(max_theoretical + 4, min_views + 4))
    
    step = 1 if allow_odd else 2
    analyses = []
    for n in range(min_views, actual_max + 1, step):
        analyses.append(analyze_view_count(n, effective_lpi, output_ppi, effective_dpi))
    
    priority = {"safe": 0, "marginal": 1, "insufficient": 2}
    analyses.sort(key=lambda a: (priority[a.feasibility], -a.n_views))
    return analyses


# ============================================================
# Camera Positions derived from Lens Geometry
# ============================================================

def compute_camera_positions(lens: LensProfile, n_views: int,
                             viewing_distance_mm: float) -> np.ndarray:
    """Compute virtual camera positions derived from lens geometry.
    
    Accurately centers the array at 0.0 mm whether n_views is odd or even.
    """
    p = get_lens_pitch_mm(lens)
    f_eff = get_effective_focal_length(lens)
    
    positions = np.zeros(n_views, dtype=np.float64)
    for k in range(n_views):
        xi_k = p * ((k + 0.5) / float(n_views) - 0.5)
        theta_k = math.atan(xi_k / f_eff)
        positions[k] = viewing_distance_mm * math.tan(theta_k)
    
    # Ensure exact symmetric centering around 0.0
    center_offset = (positions[0] + positions[-1]) / 2.0
    positions -= center_offset
    return positions


def compute_camera_baseline(lens: LensProfile, n_views: int,
                            viewing_distance_mm: float) -> float:
    """Compute total camera baseline in mm (lateral span from view 0 to view N-1)."""
    positions = compute_camera_positions(lens, n_views, viewing_distance_mm)
    return float(positions[-1] - positions[0])


def compute_camera_steps(lens: LensProfile, n_views: int,
                         viewing_distance_mm: float) -> np.ndarray:
    """Compute step sizes between adjacent cameras in mm."""
    positions = compute_camera_positions(lens, n_views, viewing_distance_mm)
    return np.diff(positions)


# ============================================================
# Parallax Budget & Strict Effect Validation
# ============================================================

EFFECT_STRENGTH_MAP: Dict[str, float] = {
    "subtle": 0.20,
    "natural": 0.35,
    "balanced": 0.55,
    "strong": 0.75,
    "extreme": 0.95,
}


def parse_effect_strength(effect_strength: Any) -> float:
    """Parse and validate effect strength.
    
    Raises ValueError on unknown effect names (prevents silent fallback bugs).
    """
    if isinstance(effect_strength, (int, float)):
        val = float(effect_strength)
        if not (0.05 <= val <= 1.0):
            raise ValueError(f"Numeric effect strength must be between 0.05 and 1.0, got {val}")
        return val
    
    name = str(effect_strength).strip().lower()
    if name not in EFFECT_STRENGTH_MAP:
        allowed = list(EFFECT_STRENGTH_MAP.keys())
        raise ValueError(f"Unknown effect strength '{effect_strength}'. Allowed presets: {allowed} or numeric float.")
    return EFFECT_STRENGTH_MAP[name]


def compute_max_parallax_pixels(effective_lpi: float, output_ppi: int) -> float:
    """Compute maximum safe parallax in pixels (one lenticule width)."""
    return float(output_ppi) / float(effective_lpi)


def compute_effective_parallax(effective_lpi: float, output_ppi: int,
                               effect_strength: Any) -> float:
    """Compute effective parallax budget in pixels."""
    max_px = compute_max_parallax_pixels(effective_lpi, output_ppi)
    factor = parse_effect_strength(effect_strength)
    return max_px * factor


def compute_perceptual_depth_mm(parallax_mm: float, viewing_distance_mm: float,
                                eye_separation_mm: float = 63.0) -> float:
    """Estimate perceptual 3D depth in mm."""
    return float(parallax_mm * viewing_distance_mm / (eye_separation_mm + parallax_mm))


# ============================================================
# Disparity Computation & Zero-Parallax Mechanics
# ============================================================

def resolve_zpp_depth(depth_map: np.ndarray,
                      selection_mask: Optional[np.ndarray] = None,
                      mode: str = "surface",
                      offset: float = 0.15,
                      default_zpp: float = 0.5) -> float:
    """Compute zero-parallax plane (ZPP) depth based on subject and mode.
    
    Depth convention: 1.0 = near/front, 0.0 = far/back.
    Disparity: d(x,y) = depth - zpp. Positive disparity pops out!
    
    Modes:
    - 'surface': ZPP exactly on subject. Subject appears at the print plane (d=0).
    - 'front': Subject pops out toward viewer!
               For d_subject > 0, we require zpp < subject_depth.
               Therefore: zpp = subject_depth - offset!
    - 'behind': Subject sinks behind the print plane into the screen!
                For d_subject < 0, we require zpp > subject_depth.
                Therefore: zpp = subject_depth + offset!
    """
    if selection_mask is not None and selection_mask.any():
        subject_depth = float(np.median(depth_map[selection_mask > 0]))
    else:
        # Fallback to central region
        h, w = depth_map.shape[:2]
        center = depth_map[h//3:2*h//3, w//3:2*w//3]
        subject_depth = float(np.median(center)) if center.size > 0 else default_zpp
    
    mode_clean = str(mode).strip().lower()
    if mode_clean == "surface":
        return float(np.clip(subject_depth, 0.05, 0.95))
    elif mode_clean == "front":
        # POP-OUT: ZPP sits BEHIND the subject (smaller depth value in white=near)
        return float(np.clip(subject_depth - offset, 0.05, 0.95))
    elif mode_clean == "behind":
        # SINK-IN: ZPP sits IN FRONT OF the subject (larger depth value in white=near)
        return float(np.clip(subject_depth + offset, 0.05, 0.95))
    else:
        raise ValueError(f"Unknown zpp_mode '{mode}'. Allowed: 'surface', 'front', 'behind'")


def compute_disparity_map_relative(depth_normalized: np.ndarray,
                                   zpp_depth: float,
                                   parallax_budget: float,
                                   front_ratio: float = 0.4,
                                   curve_fn: str = "linear",
                                   gamma: float = 1.0) -> np.ndarray:
    """Compute disparity map from normalized depth map [0, 1].
    
    Positive disparity = foreground / pop-out.
    Negative disparity = background / depth sink.
    """
    raw = depth_normalized - zpp_depth
    
    if curve_fn == "gamma" and abs(gamma - 1.0) > 1e-4:
        curved = np.sign(raw) * (np.abs(raw) ** gamma)
    elif curve_fn == "sigmoid":
        beta = 5.0
        curved = 2.0 / (1.0 + np.exp(-beta * raw)) - 1.0
    else:
        curved = raw
    
    disparity = parallax_budget * curved
    d_front = parallax_budget * front_ratio
    d_back = parallax_budget * (1.0 - front_ratio)
    return np.clip(disparity, -d_back, d_front).astype(np.float32)


def compute_view_shifts(disparity: np.ndarray, n_views: int) -> List[np.ndarray]:
    """Compute per-pixel horizontal shift maps for all views."""
    if n_views <= 1:
        return [np.zeros_like(disparity)]
    
    shifts = []
    for k in range(n_views):
        s_k = (k / (n_views - 1.0)) - 0.5
        shifts.append(s_k * disparity)
    return shifts


# ============================================================
# Output Dimensions & Print Job Summary
# ============================================================

def compute_output_dimensions(print_width_mm: float, print_height_mm: float,
                              output_ppi: int,
                              bleed_mm: float = 0.0) -> Tuple[int, int]:
    """Compute output image dimensions in pixels."""
    total_w_mm = print_width_mm + 2.0 * bleed_mm
    total_h_mm = print_height_mm + 2.0 * bleed_mm
    
    w_px = int(math.ceil(total_w_mm * output_ppi / 25.4))
    h_px = int(math.ceil(total_h_mm * output_ppi / 25.4))
    return w_px, h_px


def compute_print_job_summary(job: PrintJob) -> Dict[str, Any]:
    """Generate a comprehensive summary for a print job using unified optics."""
    lens = job.lens_profile
    printer = job.printer_profile
    
    eff_lpi = get_effective_lpi(lens, job.viewing_distance_mm)
    eff_focal = get_effective_focal_length(lens)
    focal_estimated = is_focal_length_estimated(lens)
    viewing_angle = get_viewing_angle(lens)
    pitch_mm = get_lens_pitch_mm(lens)
    
    # Unified view count calculation matching ParallaxCalculator
    all_analyses = recommend_view_counts(
        eff_lpi, printer.output_raster_ppi, printer.measured_effective_dpi
    )
    
    if job.view_count is not None and job.view_count > 0:
        n_views = job.view_count
        view_analysis = analyze_view_count(
            n_views, eff_lpi, printer.output_raster_ppi, printer.measured_effective_dpi
        )
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
            else:
                n_views = 4
                view_analysis = analyze_view_count(
                    4, eff_lpi, printer.output_raster_ppi, printer.measured_effective_dpi
                )
    
    max_parallax = compute_max_parallax_pixels(eff_lpi, printer.output_raster_ppi)
    eff_parallax = compute_effective_parallax(eff_lpi, printer.output_raster_ppi, job.effect_strength)
    parallax_mm = eff_parallax * 25.4 / printer.output_raster_ppi
    perceptual_depth = compute_perceptual_depth_mm(parallax_mm, job.viewing_distance_mm)
    
    camera_positions = compute_camera_positions(lens, n_views, job.viewing_distance_mm)
    baseline = compute_camera_baseline(lens, n_views, job.viewing_distance_mm)
    
    out_w, out_h = compute_output_dimensions(
        job.print_width_mm, job.print_height_mm, printer.output_raster_ppi, job.bleed_mm
    )
    
    strength_factor = parse_effect_strength(job.effect_strength)
    
    warnings = []
    if focal_estimated:
        warnings.append("Focal length uses thickness approximation. Pitch test recommended.")
    if lens.calibrated_lpi is None:
        warnings.append("Using nominal LPI. Optical pitch calibration strongly recommended.")
    if strength_factor >= 0.90:
        warnings.append("High parallax budget (>=90%) may cause crosstalk / ghosting.")
    if view_analysis.feasibility == "marginal":
        warnings.append(f"View count {n_views} is marginal: {view_analysis.notes}")
    elif view_analysis.feasibility == "insufficient":
        warnings.append(f"View count {n_views} is physically insufficient: {view_analysis.notes}")
    
    return {
        "effective_lpi": eff_lpi,
        "effective_focal_length_mm": eff_focal,
        "focal_length_estimated": focal_estimated,
        "viewing_angle_deg": viewing_angle,
        "lens_pitch_mm": pitch_mm,
        "n_views": n_views,
        "view_analysis": view_analysis,
        "all_view_analyses": all_analyses,
        "max_parallax_px": max_parallax,
        "effective_parallax_px": eff_parallax,
        "parallax_mm": parallax_mm,
        "perceptual_depth_mm": perceptual_depth,
        "camera_positions_mm": camera_positions.tolist(),
        "camera_baseline_mm": baseline,
        "output_width_px": out_w,
        "output_height_px": out_h,
        "effect_strength": job.effect_strength,
        "strength_factor": strength_factor,
        "warnings": warnings,
    }
