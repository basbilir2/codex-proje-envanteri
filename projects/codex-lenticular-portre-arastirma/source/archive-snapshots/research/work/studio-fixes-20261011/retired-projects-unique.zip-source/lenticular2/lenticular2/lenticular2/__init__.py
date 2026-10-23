"""Lenticular 2: Precision Optical Prepress and Multi-View Synthesis Engine.

Version: 2.0.0
"""

__version__ = "2.0.0"

from lenticular2.utils.math_utils import (
    LensProfile, PrinterProfile, PrintJob,
    get_effective_lpi, get_lens_pitch_mm, get_viewing_angle,
    recommend_view_counts, compute_print_job_summary,
)
from lenticular2.core.parallax_calculator import ParallaxCalculator, ParallaxPlan
from lenticular2.core.depth_optimizer import DepthOptimizer
from lenticular2.core.view_generator_dibr import generate_views_dibr
from lenticular2.core.interlacing import interlace, interlace_standard, interlace_subpixel
from lenticular2.calibration.pitch_test import generate_pitch_test_pattern, generate_registration_test
from lenticular2.analysis.scene_analyzer import SceneAnalyzer, SceneAnalysisReport
from lenticular2.pipeline import ProductionPipeline, load_lens_profiles, load_printer_profiles

__all__ = [
    "LensProfile", "PrinterProfile", "PrintJob",
    "get_effective_lpi", "get_lens_pitch_mm", "get_viewing_angle",
    "recommend_view_counts", "compute_print_job_summary",
    "ParallaxCalculator", "ParallaxPlan",
    "DepthOptimizer",
    "generate_views_dibr",
    "interlace", "interlace_standard", "interlace_subpixel",
    "generate_pitch_test_pattern", "generate_registration_test",
    "SceneAnalyzer", "SceneAnalysisReport",
    "ProductionPipeline", "load_lens_profiles", "load_printer_profiles",
]
