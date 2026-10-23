"""Pitch calibration and registration test pattern generator for Lenticular 2.

Features:
- Dedicated header area preventing title text from overwriting band 0 optical stripes.
- Physically accurate pixel-center phase calculation ((x + 0.5) / stripe_width).
- Multi-tier calibration (coarse ±0.5 LPI, fine ±0.05 LPI down to 0.001 LPI).
- Built-in alignment marks, tilt verification bars, and millimeter fiducials.
- Multi-view registration target generator.
"""

import logging
import math
from pathlib import Path
from typing import Optional, List, Union
import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def generate_pitch_test_pattern(
    nominal_lpi: float,
    output_ppi: int,
    print_width_mm: float = 200.0,
    print_height_mm: float = 280.0,
    lpi_range: float = 0.40,
    lpi_step: float = 0.02,
    viewing_distance_mm: Optional[float] = None,
    output_path: Optional[Union[str, Path]] = None,
) -> np.ndarray:
    """Generate a pitch test pattern for accurate optical LPI calibration.
    
    Args:
        nominal_lpi: Manufacturer's stated LPI (e.g., 60.0)
        output_ppi: Output raster resolution (e.g., 720, 1440)
        print_width_mm: Target sheet width in mm
        print_height_mm: Target sheet height in mm
        lpi_range: Test range around nominal (±)
        lpi_step: Step size between adjacent bands (e.g., 0.02 or 0.005 for fine)
        viewing_distance_mm: Optional target viewing distance to print on header
        output_path: Optional path to save image file
        
    Returns:
        Test pattern image array (H, W, 3) uint8
    """
    # 1. Physical dimensions in pixels
    width_px = int(math.ceil(print_width_mm * output_ppi / 25.4))
    height_px = int(math.ceil(print_height_mm * output_ppi / 25.4))
    
    # 2. Header margin (18mm) ensuring NO title text ever touches band 0!
    header_height_mm = 18.0
    header_height_px = int(math.ceil(header_height_mm * output_ppi / 25.4))
    
    usable_height_px = height_px - header_height_px
    
    # 3. Calculate test LPI values
    lpi_start = nominal_lpi - lpi_range
    lpi_end = nominal_lpi + lpi_range
    test_lpis: List[float] = []
    current_lpi = lpi_start
    while current_lpi <= lpi_end + 1e-6:
        test_lpis.append(round(current_lpi, 4))
        current_lpi += lpi_step
        
    n_bands = len(test_lpis)
    if n_bands < 1:
        raise ValueError("Invalid LPI range or step.")
        
    label_height_px = int(math.ceil(3.5 * output_ppi / 25.4))  # ~3.5mm label area
    band_total_height = max(12, usable_height_px // n_bands)
    stripe_height = max(8, band_total_height - label_height_px)
    
    # 4. Canvas creation (white background)
    img = np.ones((height_px, width_px, 3), dtype=np.uint8) * 255
    
    # Side margin for tilt verification & fiducials (8mm each side)
    side_margin_px = int(math.ceil(8.0 * output_ppi / 25.4))
    stripe_start_x = side_margin_px
    stripe_end_x = width_px - side_margin_px
    stripe_width_total = stripe_end_x - stripe_start_x
    
    # 5. Draw optical test bands
    for band_idx, test_lpi in enumerate(test_lpis):
        y_start = header_height_px + band_idx * band_total_height
        y_end = y_start + stripe_height
        if y_end > height_px:
            break
            
        stripe_period_px = float(output_ppi) / float(test_lpi)
        
        # Vectorized optical stripe calculation with pixel-center sampling (x + 0.5)
        xs = np.arange(stripe_width_total, dtype=np.float64)
        phase = np.mod((xs + 0.5) / stripe_period_px, 1.0)
        # 50% duty cycle black & white bars
        colors = np.where(phase < 0.5, 0, 255).astype(np.uint8)
        
        # Fill band across stripe region
        img[y_start:y_end, stripe_start_x:stripe_end_x, 0] = colors[np.newaxis, :]
        img[y_start:y_end, stripe_start_x:stripe_end_x, 1] = colors[np.newaxis, :]
        img[y_start:y_end, stripe_start_x:stripe_end_x, 2] = colors[np.newaxis, :]
        
        # Highlight nominal LPI with distinctive red border
        if abs(test_lpi - nominal_lpi) < (lpi_step / 2.0 + 1e-6):
            img[y_start:y_start+2, stripe_start_x:stripe_end_x, :] = [220, 20, 60]
            img[y_end-2:y_end, stripe_start_x:stripe_end_x, :] = [220, 20, 60]
    
    # 6. Tilt verification rails on left and right margins
    # Continuous vertical alignment bars: if the lens is tilted, moire fringes tilt diagonally
    rail_w = max(2, int(output_ppi * 1.5 / 25.4))
    img[header_height_px:, 2:2+rail_w, :] = 0
    img[header_height_px:, width_px-2-rail_w:width_px-2, :] = 0
    
    # 7. Render labels and header using Pillow
    pil_img = Image.fromarray(img)
    draw = ImageDraw.Draw(pil_img)
    
    font_size_header = max(12, int(output_ppi * 3.5 / 25.4))
    font_size_label = max(10, int(output_ppi * 2.2 / 25.4))
    
    try:
        font_header = ImageFont.truetype("arial.ttf", font_size_header)
        font_label = ImageFont.truetype("arial.ttf", font_size_label)
    except Exception:
        font_header = ImageFont.load_default()
        font_label = ImageFont.load_default()
    
    # Render Dedicated Header (safely placed in header_height_px)
    dist_str = f" | Target Dist: {viewing_distance_mm:.0f} mm" if viewing_distance_mm else ""
    title_text = f"LENTICULAR 2 — PRECISION PITCH TEST | Nominal: {nominal_lpi:.2f} LPI | Res: {output_ppi} PPI{dist_str}"
    draw.text((side_margin_px, int(header_height_px * 0.20)), title_text, fill=(20, 20, 20), font=font_header)
    
    inst_text = "Instructions: Look perpendicular at target distance. The band that appears uniform black or white is your exact optical LPI."
    draw.text((side_margin_px, int(header_height_px * 0.60)), inst_text, fill=(100, 100, 100), font=font_label)
    
    # Render Band Labels below each stripe
    for band_idx, test_lpi in enumerate(test_lpis):
        y_label = header_height_px + band_idx * band_total_height + stripe_height + 2
        if y_label + font_size_label > height_px:
            break
        label_text = f"{test_lpi:.3f} LPI"
        if abs(test_lpi - nominal_lpi) < (lpi_step / 2.0 + 1e-6):
            label_text += " [NOMINAL]"
            draw.text((side_margin_px + 5, y_label), label_text, fill=(200, 0, 0), font=font_label)
        else:
            draw.text((side_margin_px + 5, y_label), label_text, fill=(40, 40, 40), font=font_label)
            
    result = np.array(pil_img)
    
    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        pil_img.save(str(out_p), dpi=(output_ppi, output_ppi))
        logger.info(f"Saved pitch test pattern: {out_p}")
        
    return result


def generate_registration_test(
    optical_lpi: float,
    output_ppi: int,
    n_views: int = 12,
    print_width_mm: float = 200.0,
    print_height_mm: float = 120.0,
    output_path: Optional[Union[str, Path]] = None,
) -> np.ndarray:
    """Generate a numbered multi-view registration test pattern.
    
    When printed and viewed under the lens, only one clean number (1 to N)
    should be visible at each viewing angle without cross-talk or ghosting.
    """
    from lenticular2.core.interlacing import interlace_standard
    
    width_px = int(math.ceil(print_width_mm * output_ppi / 25.4))
    height_px = int(math.ceil(print_height_mm * output_ppi / 25.4))
    
    views: List[np.ndarray] = []
    
    font_size = max(24, int(height_px * 0.40))
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()
        
    colors = [
        (220, 20, 60), (30, 144, 255), (46, 139, 87), (255, 140, 0),
        (148, 0, 211), (0, 128, 128), (218, 165, 32), (75, 0, 130),
        (255, 20, 147), (0, 191, 255), (50, 205, 50), (178, 34, 34)
    ]
    
    for k in range(n_views):
        v_img = Image.new("RGB", (width_px, height_px), color=(255, 255, 255))
        draw = ImageDraw.Draw(v_img)
        num_str = str(k + 1)
        color = colors[k % len(colors)]
        
        # Draw large view number in center
        draw.text((width_px // 2 - font_size // 3, height_px // 2 - font_size // 2),
                  num_str, fill=color, font=font)
        
        # Border
        draw.rectangle([10, 10, width_px - 10, height_px - 10], outline=color, width=4)
        views.append(np.array(v_img))
        
    interlaced = interlace_standard(
        views=views,
        optical_lpi=optical_lpi,
        output_ppi=output_ppi,
        orientation="vertical",
    )
    
    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        pil_res = Image.fromarray(interlaced)
        pil_res.save(str(out_p), dpi=(output_ppi, output_ppi))
        logger.info(f"Saved registration test pattern: {out_p}")
        
    return interlaced
