"""Comprehensive Unit Tests for Lenticular 2 Engine.

Verifies all 10 optical, mathematical, and pipeline fixes.
"""

import unittest
import numpy as np
from pathlib import Path
from tempfile import TemporaryDirectory

from lenticular2.utils.math_utils import (
    LensProfile, PrinterProfile, PrintJob,
    resolve_zpp_depth, compute_disparity_map_relative,
    parse_effect_strength, recommend_view_counts,
    compute_print_job_summary, get_effective_lpi,
)
from lenticular2.utils.image_utils import (
    normalize_depth, load_image, save_image,
)
from lenticular2.core.parallax_calculator import ParallaxCalculator
from lenticular2.core.depth_optimizer import DepthOptimizer
from lenticular2.core.interlacing import interlace, interlace_standard
from lenticular2.core.view_generator_dibr import generate_views_dibr
from lenticular2.calibration.pitch_test import generate_pitch_test_pattern


class TestLenticular2Fixes(unittest.TestCase):
    
    def setUp(self):
        self.lens = LensProfile(
            name="Test 60 LPI",
            nominal_lpi=60.0,
            thickness_mm=1.2,
            refractive_index=1.57,
            orientation="vertical",
        )
        self.printer = PrinterProfile(
            name="Test Printer 720",
            output_raster_ppi=720,
        )
        self.job = PrintJob(
            lens_profile=self.lens,
            printer_profile=self.printer,
            print_width_mm=100.0,
            print_height_mm=100.0,
            viewing_distance_mm=400.0,
        )

    # ----------------------------------------------------
    # FIX 1: ZPP Front / Behind Direction & Disparity Sign
    # ----------------------------------------------------
    def test_fix1_zpp_front_behind_direction(self):
        # In normalized depth: 1.0 = near, 0.0 = far.
        # Subject is at 0.70.
        depth_map = np.full((50, 50), 0.70, dtype=np.float32)
        
        # 'front' mode (subject pops out):
        # To make disparity positive (d > 0), ZPP must be behind subject (ZPP < 0.70).
        zpp_front = resolve_zpp_depth(depth_map, mode="front", offset=0.15)
        self.assertAlmostEqual(zpp_front, 0.55, places=2)
        
        disp_front = compute_disparity_map_relative(depth_map, zpp_depth=zpp_front, parallax_budget=10.0)
        # Disparity of subject MUST be positive (pops out)!
        self.assertGreater(disp_front.mean(), 0.0, "Front mode disparity must be positive (pop-out)!")
        
        # 'behind' mode (subject recedes into screen):
        # To make disparity negative (d < 0), ZPP must be in front of subject (ZPP > 0.70).
        zpp_behind = resolve_zpp_depth(depth_map, mode="behind", offset=0.15)
        self.assertAlmostEqual(zpp_behind, 0.85, places=2)
        
        disp_behind = compute_disparity_map_relative(depth_map, zpp_depth=zpp_behind, parallax_budget=10.0)
        # Disparity of subject MUST be negative (recedes)!
        self.assertLess(disp_behind.mean(), 0.0, "Behind mode disparity must be negative (recedes)!")

    # ----------------------------------------------------
    # FIX 2: Interlacing Registration Offset & Horizontal Direction
    # ----------------------------------------------------
    def test_fix2_registration_offset_and_horizontal_lens(self):
        # Create 4 distinct views
        views = [np.full((32, 32, 3), k * 60, dtype=np.uint8) for k in range(4)]
        
        # Horizontal lens: offset = 0.0 vs offset = 0.5 mm
        out_no_offset = interlace_standard(
            views, optical_lpi=60.0, output_ppi=720,
            orientation="horizontal", registration_offset_mm=0.0
        )
        out_with_offset = interlace_standard(
            views, optical_lpi=60.0, output_ppi=720,
            orientation="horizontal", registration_offset_mm=0.5
        )
        # In the old bug, horizontal lens ignored registration_offset_mm.
        # Here they MUST be different!
        self.assertFalse(np.array_equal(out_no_offset, out_with_offset),
                         "Registration offset must shift horizontal lenticules!")
        
        # Also verify through interlace(views, job)
        job1 = PrintJob(self.lens, self.printer, 100, 100, registration_offset_mm=0.0)
        job2 = PrintJob(self.lens, self.printer, 100, 100, registration_offset_mm=0.5)
        res1 = interlace(views, job1)
        res2 = interlace(views, job2)
        self.assertFalse(np.array_equal(res1, res2),
                         "PrintJob.registration_offset_mm must pass through interlace()!")

    # ----------------------------------------------------
    # FIX 3: Default use_subpixel_interlacing is False
    # ----------------------------------------------------
    def test_fix3_subpixel_default_is_false(self):
        job = PrintJob(self.lens, self.printer, 100, 100)
        self.assertFalse(job.use_subpixel_interlacing,
                         "use_subpixel_interlacing must default to False for UV Flatbed safety!")

    # ----------------------------------------------------
    # FIX 4: View Count Consistency and Odd View Support
    # ----------------------------------------------------
    def test_fix4_view_count_unification_and_odd_views(self):
        # Odd view count support (e.g. 9 views)
        analyses = recommend_view_counts(effective_lpi=60.0, output_ppi=720, allow_odd=True)
        view_counts = [a.n_views for a in analyses]
        self.assertTrue(any(v % 2 != 0 for v in view_counts),
                        "recommend_view_counts must support odd view counts!")
        
        # Calculator vs summary view selection unification
        calc = ParallaxCalculator(self.job)
        plan = calc.plan
        summary = compute_print_job_summary(self.job)
        self.assertEqual(plan.n_views, summary["n_views"],
                         "ParallaxCalculator and compute_print_job_summary must select identical view counts!")

    # ----------------------------------------------------
    # FIX 5: Strict Effect Name Validation
    # ----------------------------------------------------
    def test_fix5_effect_validation_no_silent_fallback(self):
        # Known presets work
        self.assertAlmostEqual(parse_effect_strength("balanced"), 0.55)
        self.assertAlmostEqual(parse_effect_strength("strong"), 0.75)
        
        # Invalid preset raises ValueError (instead of silent fallback)
        with self.assertRaises(ValueError):
            parse_effect_strength("mega")

    # ----------------------------------------------------
    # FIX 6: Depth Normalization Polarity Safety
    # ----------------------------------------------------
    def test_fix6_depth_normalization_no_accidental_inversion(self):
        # Scene with bright sky borders (1.0) and dark subject in center (0.2)
        depth = np.ones((100, 100), dtype=np.float32)
        depth[30:70, 30:70] = 0.2
        
        # Default auto_detect_depth_polarity=False MUST NOT invert the scene!
        norm = normalize_depth(depth, white_near=True, auto_detect_depth_polarity=False)
        self.assertAlmostEqual(float(norm[50, 50]), 0.0, places=2,
                               msg="Center subject must remain at lower value without auto-invert!")
        self.assertAlmostEqual(float(norm[0, 0]), 1.0, places=2)

    # ----------------------------------------------------
    # FIX 7: Vectorized DIBR Speed & Correctness
    # ----------------------------------------------------
    def test_fix7_vectorized_dibr(self):
        img = np.zeros((64, 64, 3), dtype=np.uint8)
        img[20:44, 20:44] = [255, 0, 0]  # red square
        disp = np.zeros((64, 64), dtype=np.float32)
        disp[20:44, 20:44] = 6.0  # 6 px disparity
        
        views = generate_views_dibr(img, disp, n_views=6, fill_holes=True)
        self.assertEqual(len(views), 6)
        self.assertEqual(views[0].shape, (64, 64, 3))
        # Leftmost view vs rightmost view must shift laterally
        self.assertFalse(np.array_equal(views[0], views[-1]),
                         "DIBR views must exhibit lateral parallax shifts!")

    # ----------------------------------------------------
    # FIX 8: Float32 Bilateral Filtering
    # ----------------------------------------------------
    def test_fix8_float32_bilateral_filter(self):
        optimizer = DepthOptimizer(bilateral_d=5, bilateral_sigma_color=0.1)
        # Create a smooth continuous float32 ramp [0.100, 0.105] that would be ruined by 8-bit uint8
        ramp = np.linspace(0.100, 0.105, 100, dtype=np.float32)
        depth_f32 = np.tile(ramp, (50, 1))
        
        denoised = optimizer.optimize(depth_f32, denoise=True, edge_refine=False, apply_curve=False)
        self.assertEqual(denoised.dtype, np.float32)
        # Check that fine floating precision is preserved (dynamic range is intact)
        self.assertGreater(len(np.unique(denoised)), 10,
                           "Float32 bilateral filter must not quantize smooth gradients to single 8-bit bins!")

    # ----------------------------------------------------
    # FIX 9: Pitch Test Pattern Header & Pixel-Center Phase
    # ----------------------------------------------------
    def test_fix9_pitch_test_header_and_phase(self):
        pattern = generate_pitch_test_pattern(
            nominal_lpi=60.0, output_ppi=720,
            print_width_mm=100.0, print_height_mm=100.0,
            lpi_range=0.10, lpi_step=0.05
        )
        self.assertIsInstance(pattern, np.ndarray)
        self.assertEqual(pattern.shape[2], 3)
        # Header is at top: check that row 5 is NOT overwriting optical bands
        header_row = pattern[5, :, :]
        # Header text exists and is on white background, not striped moire
        self.assertGreater(header_row.mean(), 200, "Header must have clean white background!")

    # ----------------------------------------------------
    # FIX 10: Safe Image Loading (2D Grayscale in RGBA mode)
    # ----------------------------------------------------
    def test_fix10_image_loader_grayscale_rgba(self):
        with TemporaryDirectory() as tmpdir:
            gray_path = Path(tmpdir) / "gray.png"
            # Save 2D grayscale image
            gray_img = (np.ones((40, 40), dtype=np.uint8) * 128)
            save_image(gray_img, gray_path)
            
            # Loading 2D grayscale in 'rgba' mode should NOT crash with IndexError: img.shape[2]
            rgba = load_image(gray_path, mode="rgba")
            self.assertEqual(len(rgba.shape), 3)
            self.assertEqual(rgba.shape[2], 4)
            self.assertEqual(rgba.dtype, np.uint8)
            
            # Loading in 'rgb' mode
            rgb = load_image(gray_path, mode="rgb")
            self.assertEqual(len(rgb.shape), 3)
            self.assertEqual(rgb.shape[2], 3)


if __name__ == "__main__":
    unittest.main()
