"""Mathematical utilities for lenticular lens optics and print calculations.

All physical units are documented in function signatures:
- Distances: mm (millimeters) unless noted otherwise
- Angles: degrees (converted internally to radians as needed)
- Resolution: PPI/DPI/LPI as specified
- Pixels: integer or float pixel counts
"""

import math
import numpy as np
from dataclasses import dataclass, field
from typing import Optional, List, Tuple


@dataclass
class LensProfile:
    """Physical and optical properties of a lenticular lens sheet."""
    name: str
    nominal_lpi: float  # Manufacturer's stated LPI
    calibrated_lpi: Optional[float] = None  # Measured optical LPI from pitch test
    thickness_mm: float = 1.0
    refractive_index: Optional[float] = None  # Typically 1.52-1.65
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
    output_raster_ppi: int  # Output file pixel density
    addressable_dpi_h: int  # Print head horizontal DPI
    addressable_dpi_v: int  # Print head vertical DPI
    measured_effective_dpi: Optional[int] = None  # After RIP, dot gain, etc.
    max_print_width_mm: float = 600.0
    max_print_height_mm: float = 400.0
    color_mode: str = "CMYK"  # "CMYK" or "RGB"
    icc_profile_path: Optional[str] = None
    notes: str = ""


@dataclass
class PrintJob:
    """Complete print job specification."""
    lens_profile: LensProfile
    printer_profile: PrinterProfile
    print_width_mm: float
    print_height_mm: float
    viewing_distance_mm: float = 400.0
    print_direction: str = "horizontal"  # Parallax direction
    effect_strength: str = "balanced"  # "natural", "balanced", "strong", "extreme"
    zpp_depth_value: float = 0.5  # Zero-parallax plane in normalized depth [0,1]
    zpp_mode: str = "surface"  # "front", "surface", "behind"
    view_count: Optional[int] = None  # None = auto-calculate
    use_subpixel_interlacing: bool = True
    depth_curve: str = "linear"  # "linear", "gamma", "sigmoid"
    depth_gamma: float = 1.0  # Only used when depth_curve="gamma"
    front_parallax_ratio: float = 0.4  # Budget split: 40% front, 60% back


# ============================================================
# Lens Optics
# ============================================================

def get_effective_lpi(lens: LensProfile, viewing_distance_mm: Optional[float] = None) -> float:
    """Get the effective (optical) LPI for interlacing.
    
    Priority:
    1. Calibrated LPI from pitch test (most accurate)
    2. Calibration data for specific viewing distance
    3. Theoretical optical LPI from nominal + viewing distance + thickness
    4. Nominal LPI (least accurate, with warning)
    
    Args:
        lens: Lens profile
        viewing_distance_mm: Viewing distance in mm (optional)
        
    Returns:
        Effective LPI value for interlacing calculations
    """
    # 1. Direct calibrated value
    if lens.calibrated_lpi is not None:
        return lens.calibrated_lpi
    
    # 2. Distance-specific calibration
    if viewing_distance_mm is not None and lens.calibration_data:
        # Find closest calibration point
        closest = min(lens.calibration_data,
                      key=lambda c: abs(c["distance_mm"] - viewing_distance_mm))
        return closest["measured_lpi"]
    
    # 3. Theoretical correction
    if viewing_distance_mm is not None and lens.thickness_mm > 0:
        # Optical LPI = Mechanical LPI × (D / (D - t))
        d = viewing_distance_mm
        t = lens.thickness_mm
        if d > t:  # Sanity check
            return lens.nominal_lpi * (d / (d - t))
    
    # 4. Fallback to nominal (should warn user)
    return lens.nominal_lpi


def get_effective_focal_length(lens: LensProfile) -> float:
    """Determine effective focal length using available data.
    
    Priority:
    1. Direct effective_focal_length_mm if provided
    2. Back focal distance if provided
    3. Derived from measured viewing angle: f = (p/2) / tan(α/2)
    4. Thin lens approximation: f ≈ thickness (with warning)
    
    Args:
        lens: Lens profile
        
    Returns:
        Effective focal length in mm
    """
    # 1. Direct value
    if lens.effective_focal_length_mm is not None:
        return lens.effective_focal_length_mm
    
    # 2. Back focal distance
    if lens.back_focal_distance_mm is not None:
        return lens.back_focal_distance_mm
    
    # 3. From measured viewing angle
    if lens.viewing_angle_measured_deg is not None:
        p = get_lens_pitch_mm(lens)
        half_angle_rad = math.radians(lens.viewing_angle_measured_deg / 2)
        if half_angle_rad > 0:
            return (p / 2) / math.tan(half_angle_rad)
    
    # 4. Thin lens approximation (warning should be issued by caller)
    return lens.thickness_mm


def get_lens_pitch_mm(lens: LensProfile) -> float:
    """Get the physical pitch width of one lenticule.
    
    Args:
        lens: Lens profile
        
    Returns:
        Pitch width in mm
    """
    lpi = lens.calibrated_lpi if lens.calibrated_lpi else lens.nominal_lpi
    return 25.4 / lpi


def get_viewing_angle(lens: LensProfile) -> float:
    """Calculate the total viewing angle of the lens.
    
    α = 2 × arctan(p / (2 × f_eff))
    
    Args:
        lens: Lens profile
        
    Returns:
        Viewing angle in degrees
    """
    if lens.viewing_angle_measured_deg is not None:
        return lens.viewing_angle_measured_deg
    
    p = get_lens_pitch_mm(lens)
    f = get_effective_focal_length(lens)
    return 2 * math.degrees(math.atan(p / (2 * f)))


def is_focal_length_estimated(lens: LensProfile) -> bool:
    """Check if focal length is using thin-lens approximation (less reliable)."""
    return (lens.effective_focal_length_mm is None and
            lens.back_focal_distance_mm is None and
            lens.viewing_angle_measured_deg is None)


# ============================================================
# View Count Analysis
# ============================================================

@dataclass
class ViewCountAnalysis:
    """Analysis result for a candidate view count."""
    n_views: int
    raster_samples_per_lenticule: float  # C_raster
    printer_dots_per_lenticule: float  # C_printer (if effective DPI known)
    raster_width_per_view: float  # w_raster/view
    printer_width_per_view: Optional[float]  # w_printer/view
    feasibility: str  # "safe", "marginal", "insufficient"
    notes: str


def analyze_view_count(n_views: int, effective_lpi: float,
                       output_ppi: int, 
                       effective_dpi: Optional[int] = None) -> ViewCountAnalysis:
    """Analyze physical feasibility of a candidate view count.
    
    Evaluates whether the printer can reliably produce the required
    stripe width for each view within a lenticule.
    
    Args:
        n_views: Candidate number of views
        effective_lpi: Calibrated or computed optical LPI
        output_ppi: Output raster PPI (perpendicular to lens lines)
        effective_dpi: Measured effective printer DPI (optional)
        
    Returns:
        ViewCountAnalysis with feasibility assessment
    """
    c_raster = output_ppi / effective_lpi
    w_raster = c_raster / n_views
    
    c_printer = None
    w_printer = None
    if effective_dpi is not None:
        c_printer = effective_dpi / effective_lpi
        w_printer = c_printer / n_views
    
    # Feasibility assessment
    if w_raster < 1.0:
        feasibility = "insufficient"
        notes = f"Raster width per view ({w_raster:.2f}) < 1.0 pixel. Not enough resolution."
    elif w_printer is not None and w_printer < 1.5:
        feasibility = "marginal"
        notes = (f"Printer dots per view ({w_printer:.2f}) < 1.5. "
                 f"Printer may not reliably distinguish views.")
    elif w_raster < 1.2:
        feasibility = "marginal"
        notes = f"Raster width per view ({w_raster:.2f}) is borderline."
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
                          max_views: int = 36) -> List[ViewCountAnalysis]:
    """Analyze all candidate view counts and return ranked recommendations.
    
    Args:
        effective_lpi: Calibrated optical LPI
        output_ppi: Output file PPI
        effective_dpi: Measured effective printer DPI
        min_views: Minimum views to consider
        max_views: Maximum views to consider
        
    Returns:
        List of ViewCountAnalysis, sorted by feasibility then view count
    """
    max_theoretical = int(output_ppi / effective_lpi)
    actual_max = min(max_views, max_theoretical + 2)  # Allow slightly over for analysis
    
    analyses = []
    for n in range(min_views, actual_max + 1, 2):  # Even numbers preferred
        analysis = analyze_view_count(n, effective_lpi, output_ppi, effective_dpi)
        analyses.append(analysis)
    
    # Sort: safe first, then by view count descending (more views = smoother)
    priority = {"safe": 0, "marginal": 1, "insufficient": 2}
    analyses.sort(key=lambda a: (priority[a.feasibility], -a.n_views))
    
    return analyses


# ============================================================
# Camera Positions from Lens Geometry
# ============================================================

def compute_camera_positions(lens: LensProfile, n_views: int,
                             viewing_distance_mm: float) -> np.ndarray:
    """Compute virtual camera positions derived from lens geometry.
    
    Each view stripe's center position within the lenticule determines
    the viewing angle, which maps to a camera position at the viewing distance.
    
    ξ_k = p × ((k + 0.5) / N - 0.5)
    θ_k ≈ arctan(ξ_k / f_eff)
    X_k = L × tan(θ_k)
    
    Args:
        lens: Lens profile
        n_views: Number of views
        viewing_distance_mm: Viewing distance in mm
        
    Returns:
        Array of camera X positions in mm, shape (n_views,)
    """
    p = get_lens_pitch_mm(lens)
    f_eff = get_effective_focal_length(lens)
    
    positions = np.zeros(n_views)
    for k in range(n_views):
        xi_k = p * ((k + 0.5) / n_views - 0.5)
        theta_k = math.atan(xi_k / f_eff)
        positions[k] = viewing_distance_mm * math.tan(theta_k)
    
    return positions


def compute_camera_baseline(lens: LensProfile, n_views: int,
                            viewing_distance_mm: float) -> float:
    """Compute total camera baseline (total lateral movement).
    
    Args:
        lens: Lens profile
        n_views: Number of views
        viewing_distance_mm: Viewing distance in mm
        
    Returns:
        Total baseline in mm (X_{N-1} - X_0)
    """
    positions = compute_camera_positions(lens, n_views, viewing_distance_mm)
    return float(positions[-1] - positions[0])


def compute_camera_steps(lens: LensProfile, n_views: int,
                         viewing_distance_mm: float) -> np.ndarray:
    """Compute inter-camera distances (steps between adjacent cameras).
    
    Args:
        lens: Lens profile
        n_views: Number of views
        viewing_distance_mm: Viewing distance in mm
        
    Returns:
        Array of step sizes in mm, shape (n_views - 1,)
    """
    positions = compute_camera_positions(lens, n_views, viewing_distance_mm)
    return np.diff(positions)


# ============================================================
# Parallax Budget
# ============================================================

EFFECT_STRENGTH_MAP = {
    "natural": 0.35,
    "balanced": 0.55,
    "strong": 0.75,
    "extreme": 0.95,
}


def compute_max_parallax_pixels(effective_lpi: float, output_ppi: int) -> float:
    """Compute maximum safe parallax in pixels (one lenticule width).
    
    Exceeding this causes ghosting/crosstalk.
    
    Args:
        effective_lpi: Calibrated optical LPI
        output_ppi: Output raster PPI
        
    Returns:
        Maximum parallax in pixels
    """
    return output_ppi / effective_lpi


def compute_effective_parallax(effective_lpi: float, output_ppi: int,
                                effect_strength: str) -> float:
    """Compute the actual parallax budget based on effect strength.
    
    Args:
        effective_lpi: Calibrated optical LPI
        output_ppi: Output raster PPI
        effect_strength: One of 'natural', 'balanced', 'strong', 'extreme'
        
    Returns:
        Effective parallax budget in pixels
    """
    max_px = compute_max_parallax_pixels(effective_lpi, output_ppi)
    strength = EFFECT_STRENGTH_MAP.get(effect_strength, 0.55)
    return max_px * strength


def compute_perceptual_depth_mm(parallax_mm: float, viewing_distance_mm: float,
                                 eye_separation_mm: float = 63.0) -> float:
    """Estimate perceptual depth from parallax and viewing distance.
    
    d_mm ≈ E × z / (L - z)  →  z ≈ d × L / (E + d)
    For small depths: z ≈ d × L / E
    
    Args:
        parallax_mm: Total parallax in mm on print surface
        viewing_distance_mm: Viewing distance in mm
        eye_separation_mm: Inter-ocular distance (default 63mm)
        
    Returns:
        Estimated perceptual depth in mm
    """
    return parallax_mm * viewing_distance_mm / (eye_separation_mm + parallax_mm)


# ============================================================
# Disparity Computation from Depth Map
# ============================================================

def compute_disparity_map_relative(depth_normalized: np.ndarray,
                                    zpp_depth: float,
                                    parallax_budget: float,
                                    front_ratio: float = 0.4,
                                    curve_fn: str = "linear",
                                    gamma: float = 1.0) -> np.ndarray:
    """Compute disparity map from normalized relative depth.
    
    d(x,y) = clip(A × g(ρ(x,y) - ρ_0), -d_back, d_front)
    
    Args:
        depth_normalized: Depth map normalized to [0, 1], white=near, black=far
        zpp_depth: Zero-parallax plane depth value in [0, 1]
        parallax_budget: Total parallax budget A in pixels
        front_ratio: Fraction of budget for foreground pop-out (default 0.4)
        curve_fn: Depth curve function: 'linear', 'gamma', 'sigmoid'
        gamma: Gamma value (only used when curve_fn='gamma')
        
    Returns:
        Disparity map in pixels (positive = foreground/pop-out, negative = background)
    """
    # Compute raw offset from zero-parallax
    raw = depth_normalized - zpp_depth
    
    # Apply depth curve
    if curve_fn == "gamma":
        curved = np.sign(raw) * np.abs(raw) ** gamma
    elif curve_fn == "sigmoid":
        beta = 5.0
        curved = 2.0 / (1.0 + np.exp(-beta * raw)) - 1.0
    else:  # linear
        curved = raw
    
    # Scale by parallax budget
    disparity = parallax_budget * curved
    
    # Clip to front/back limits
    d_front = parallax_budget * front_ratio
    d_back = parallax_budget * (1.0 - front_ratio)
    disparity = np.clip(disparity, -d_back, d_front)
    
    return disparity


def compute_disparity_map_metric(depth_meters: np.ndarray,
                                  zpp_depth_meters: float,
                                  baseline_mm: float,
                                  focal_length_px: float,
                                  max_parallax_px: float) -> np.ndarray:
    """Compute disparity map from metric depth.
    
    d_px = f_px × B × (1/Z - 1/Z_0)
    
    Args:
        depth_meters: Depth map in meters
        zpp_depth_meters: Zero-parallax plane depth in meters
        baseline_mm: Camera baseline in mm
        focal_length_px: Virtual camera focal length in pixels
        max_parallax_px: Maximum allowed parallax in pixels
        
    Returns:
        Disparity map in pixels
    """
    # Avoid division by zero
    safe_depth = np.maximum(depth_meters, 0.001)
    
    baseline_m = baseline_mm / 1000.0
    disparity = focal_length_px * baseline_m * (1.0 / safe_depth - 1.0 / zpp_depth_meters)
    
    return np.clip(disparity, -max_parallax_px, max_parallax_px)


def compute_view_shifts(disparity: np.ndarray, n_views: int) -> List[np.ndarray]:
    """Compute per-pixel horizontal shift for each view.
    
    s_k = k/(N-1) - 0.5
    x_k(x,y) = s_k × d(x,y)
    
    Args:
        disparity: Disparity map (total disparity between extreme views)
        n_views: Number of views
        
    Returns:
        List of shift maps, one per view. Each has same shape as disparity.
    """
    shifts = []
    for k in range(n_views):
        s_k = k / (n_views - 1) - 0.5
        shift = s_k * disparity
        shifts.append(shift)
    return shifts


# ============================================================
# Output Dimensions
# ============================================================

def compute_output_dimensions(print_width_mm: float, print_height_mm: float,
                               output_ppi: int, 
                               bleed_mm: float = 0.0) -> Tuple[int, int]:
    """Compute output image dimensions in pixels.
    
    Args:
        print_width_mm: Print width in mm
        print_height_mm: Print height in mm
        output_ppi: Output raster PPI
        bleed_mm: Bleed margin on each side in mm
        
    Returns:
        (width_px, height_px) tuple
    """
    total_width_mm = print_width_mm + 2 * bleed_mm
    total_height_mm = print_height_mm + 2 * bleed_mm
    
    width_px = int(math.ceil(total_width_mm * output_ppi / 25.4))
    height_px = int(math.ceil(total_height_mm * output_ppi / 25.4))
    
    return width_px, height_px


def compute_print_job_summary(job: PrintJob) -> dict:
    """Generate a complete summary of all computed parameters for a print job.
    
    Args:
        job: Complete print job specification
        
    Returns:
        Dictionary with all computed values
    """
    lens = job.lens_profile
    printer = job.printer_profile
    
    eff_lpi = get_effective_lpi(lens, job.viewing_distance_mm)
    eff_focal = get_effective_focal_length(lens)
    focal_estimated = is_focal_length_estimated(lens)
    viewing_angle = get_viewing_angle(lens)
    pitch_mm = get_lens_pitch_mm(lens)
    
    # Determine view count
    if job.view_count is not None:
        n_views = job.view_count
    else:
        # Auto: largest safe view count
        analyses = recommend_view_counts(
            eff_lpi, printer.output_raster_ppi, printer.measured_effective_dpi
        )
        safe = [a for a in analyses if a.feasibility == "safe"]
        n_views = safe[0].n_views if safe else 8
    
    # Parallax
    max_parallax = compute_max_parallax_pixels(eff_lpi, printer.output_raster_ppi)
    eff_parallax = compute_effective_parallax(eff_lpi, printer.output_raster_ppi,
                                              job.effect_strength)
    parallax_mm = eff_parallax * 25.4 / printer.output_raster_ppi
    perceptual_depth = compute_perceptual_depth_mm(parallax_mm, job.viewing_distance_mm)
    
    # Camera
    camera_positions = compute_camera_positions(lens, n_views, job.viewing_distance_mm)
    baseline = compute_camera_baseline(lens, n_views, job.viewing_distance_mm)
    
    # Output dimensions
    out_w, out_h = compute_output_dimensions(
        job.print_width_mm, job.print_height_mm, printer.output_raster_ppi
    )
    
    # View analysis
    view_analysis = analyze_view_count(
        n_views, eff_lpi, printer.output_raster_ppi, printer.measured_effective_dpi
    )
    
    warnings = []
    if focal_estimated:
        warnings.append("Focal length uses thin-lens approximation. "
                        "Pitch test and viewing test recommended for accuracy.")
    if lens.calibrated_lpi is None:
        warnings.append("Using nominal LPI. Pitch calibration recommended.")
    if job.effect_strength == "extreme":
        warnings.append("Extreme parallax may cause ghosting. "
                        "Small test print recommended.")
    if view_analysis.feasibility == "marginal":
        warnings.append(f"View count {n_views} is marginal: {view_analysis.notes}")
    
    return {
        "effective_lpi": eff_lpi,
        "effective_focal_length_mm": eff_focal,
        "focal_length_estimated": focal_estimated,
        "viewing_angle_deg": viewing_angle,
        "lens_pitch_mm": pitch_mm,
        "n_views": n_views,
        "view_analysis": view_analysis,
        "max_parallax_px": max_parallax,
        "effective_parallax_px": eff_parallax,
        "parallax_mm": parallax_mm,
        "perceptual_depth_mm": perceptual_depth,
        "camera_positions_mm": camera_positions.tolist(),
        "camera_baseline_mm": baseline,
        "output_width_px": out_w,
        "output_height_px": out_h,
        "effect_strength": job.effect_strength,
        "strength_factor": EFFECT_STRENGTH_MAP.get(job.effect_strength, 0.55),
        "warnings": warnings,
    }
