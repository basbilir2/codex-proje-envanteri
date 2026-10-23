"""Pitch calibration test pattern generator.

Generates test patterns for measuring the actual optical LPI
of a lens + printer + substrate combination.
"""

import logging
import math
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


def generate_pitch_test_pattern(
    nominal_lpi: float,
    output_ppi: int,
    print_width_mm: float = 200.0,
    print_height_mm: float = 280.0,
    lpi_range: float = 0.5,
    lpi_step: float = 0.02,
    output_path: Optional[str] = None,
) -> np.ndarray:
    """Generate a pitch test pattern for lens calibration.
    
    Creates alternating black/white stripes at varying LPI values
    around the nominal LPI. When printed and viewed through the lens,
    the band that flashes cleanly between black and white indicates
    the true optical LPI.
    
    Args:
        nominal_lpi: Manufacturer's stated LPI
        output_ppi: Output raster PPI for the test pattern
        print_width_mm: Physical width of test pattern in mm
        print_height_mm: Physical height of test pattern in mm
        lpi_range: Range around nominal to test (±)
        lpi_step: Step size between test LPI values
        output_path: Optional path to save the pattern
        
    Returns:
        Test pattern image as numpy array (RGB)
    """
    # Calculate test LPI values
    lpi_start = nominal_lpi - lpi_range
    lpi_end = nominal_lpi + lpi_range
    test_lpis = []
    lpi = lpi_start
    while lpi <= lpi_end + 1e-6:
        test_lpis.append(round(lpi, 4))
        lpi += lpi_step
    
    n_bands = len(test_lpis)
    logger.info(f"Generating pitch test: {n_bands} bands from {lpi_start:.2f} to {lpi_end:.2f} LPI")
    
    # Image dimensions in pixels
    width_px = int(math.ceil(print_width_mm * output_ppi / 25.4))
    height_px = int(math.ceil(print_height_mm * output_ppi / 25.4))
    
    # Each band gets equal height
    label_height_px = int(8 * output_ppi / 72)  # ~8pt text height
    band_total_height = height_px // n_bands
    stripe_height = band_total_height - label_height_px
    
    if stripe_height < 10:
        # Reduce number of bands if they're too thin
        lpi_step = lpi_step * 2
        test_lpis = []
        lpi = lpi_start
        while lpi <= lpi_end + 1e-6:
            test_lpis.append(round(lpi, 4))
            lpi += lpi_step
        n_bands = len(test_lpis)
        band_total_height = height_px // n_bands
        stripe_height = band_total_height - label_height_px
    
    # Create image
    img = np.ones((height_px, width_px, 3), dtype=np.uint8) * 255
    
    for band_idx, test_lpi in enumerate(test_lpis):
        y_start = band_idx * band_total_height
        y_end = y_start + stripe_height
        
        if y_end > height_px:
            break
        
        # Generate stripes at this LPI
        stripe_width_px = output_ppi / test_lpi  # pixels per lenticule
        
        for x in range(width_px):
            # Phase within lenticule
            phase = (x / stripe_width_px) % 1.0
            # Black or white stripe (50% duty cycle)
            color = 0 if phase < 0.5 else 255
            img[y_start:y_end, x, :] = color
        
        # Highlight nominal LPI band
        if abs(test_lpi - nominal_lpi) < lpi_step / 2:
            # Add red border to nominal
            img[y_start:y_start+2, :, :] = [255, 0, 0]
            img[y_end-2:y_end, :, :] = [255, 0, 0]
    
    # Add labels using PIL
    pil_img = Image.fromarray(img)
    draw = ImageDraw.Draw(pil_img)
    
    try:
        font = ImageFont.truetype("arial.ttf", max(10, label_height_px - 2))
    except (OSError, IOError):
        font = ImageFont.load_default()
    
    for band_idx, test_lpi in enumerate(test_lpis):
        y_start = band_idx * band_total_height + stripe_height
        label = f"{test_lpi:.2f} LPI"
        if abs(test_lpi - nominal_lpi) < lpi_step / 2:
            label += " (nominal)"
        draw.text((10, y_start + 2), label, fill=(0, 0, 0), font=font)
    
    # Title
    draw.text((10, 5), f"Pitch Test — Nominal: {nominal_lpi:.1f} LPI | PPI: {output_ppi}",
              fill=(128, 0, 0), font=font)
    
    result = np.array(pil_img)
    
    # Save if path provided
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        pil_img.save(str(path), dpi=(output_ppi, output_ppi))
        logger.info(f"Pitch test pattern saved: {path}")
    
    return result


def generate_registration_test(
    optical_lpi: float,
    output_ppi: int,
    n_views: int,
    print_width_mm: float = 200.0,
    print_height_mm: float = 100.0,
    output_path: Optional[str] = None,
) -> np.ndarray:
    """Generate a registration test pattern.
    
    Creates an interlaced pattern where each view shows its number.
    When viewed through the lens, a single clean number should be visible
    at each angle, confirming correct interlacing alignment.
    
    Args:
        optical_lpi: Calibrated optical LPI
        output_ppi: Output PPI
        n_views: Number of views
        print_width_mm: Print width in mm
        print_height_mm: Print height in mm
        output_path: Optional save path
        
    Returns:
        Registration test image (RGB)
    """
    width_px = int(math.ceil(print_width_mm * output_ppi / 25.4))
    height_px = int(math.ceil(print_height_mm * output_ppi / 25.4))
    
    # Create colored views with view numbers
    colors = [
        (255, 50, 50), (50, 200, 50), (50, 50, 255),
        (255, 200, 50), (50, 200, 200), (200, 50, 200),
        (255, 128, 0), (0, 128, 255), (128, 255, 0),
        (255, 0, 128), (128, 0, 255), (0, 255, 128),
    ]
    
    views = []
    for k in range(n_views):
        view = np.zeros((height_px, width_px, 3), dtype=np.uint8)
        color = colors[k % len(colors)]
        view[:] = color
        
        # Add view number text
        pil_view = Image.fromarray(view)
        draw = ImageDraw.Draw(pil_view)
        try:
            font_size = max(20, height_px // 4)
            font = ImageFont.truetype("arial.ttf", font_size)
        except (OSError, IOError):
            font = ImageFont.load_default()
        
        text = str(k + 1)
        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        # Tile the number across the view
        for tx in range(0, width_px, text_w + 40):
            for ty in range(0, height_px, text_h + 20):
                draw.text((tx, ty), text, fill=(255, 255, 255), font=font)
        
        views.append(np.array(pil_view))
    
    # Interlace
    from core.interlacing import interlace_standard
    result = interlace_standard(views, optical_lpi, output_ppi)
    
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(result).save(str(path), dpi=(output_ppi, output_ppi))
        logger.info(f"Registration test saved: {path}")
    
    return result
