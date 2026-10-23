"""Command-Line Interface for Lenticular 2."""

import argparse
import json
import sys
from pathlib import Path

from lenticular2.utils.math_utils import LensProfile, PrinterProfile, PrintJob
from lenticular2.core.parallax_calculator import ParallaxCalculator
from lenticular2.calibration.pitch_test import generate_pitch_test_pattern, generate_registration_test
from lenticular2.analysis.scene_analyzer import SceneAnalyzer
from lenticular2.utils.image_utils import load_image
from lenticular2.pipeline import (
    load_lens_profiles, load_printer_profiles, ProductionPipeline
)


def main():
    parser = argparse.ArgumentParser(
        prog="lenticular2",
        description="Lenticular 2: Precision Optical Prepress and Multi-View Synthesis Engine"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 1. Pitch Test Command
    cmd_pitch = subparsers.add_parser("pitch-test", help="Generate precision optical pitch test pattern")
    cmd_pitch.add_argument("--lpi", type=float, default=60.0, help="Nominal LPI")
    cmd_pitch.add_argument("--ppi", type=int, default=720, help="Printer raster PPI")
    cmd_pitch.add_argument("--width", type=float, default=200.0, help="Print width in mm")
    cmd_pitch.add_argument("--height", type=float, default=280.0, help="Print height in mm")
    cmd_pitch.add_argument("--range", type=float, default=0.40, help="LPI range (±)")
    cmd_pitch.add_argument("--step", type=float, default=0.02, help="LPI step size")
    cmd_pitch.add_argument("--dist", type=float, default=400.0, help="Target viewing distance in mm")
    cmd_pitch.add_argument("--output", type=str, default="pitch_test_pattern.png", help="Output file path")
    
    # 2. Scene Analyze Command
    cmd_analyze = subparsers.add_parser("analyze", help="Inspect image & depth map for optimal parameters")
    cmd_analyze.add_argument("--image", type=str, required=True, help="Input RGB image")
    cmd_analyze.add_argument("--depth", type=str, required=True, help="Input depth map")
    cmd_analyze.add_argument("--lpi", type=float, default=60.0, help="Target lens LPI")
    cmd_analyze.add_argument("--ppi", type=int, default=720, help="Target printer PPI")
    
    # 3. Production Render Command
    cmd_render = subparsers.add_parser("render", help="Run end-to-end multi-view DIBR and interlacing")
    cmd_render.add_argument("--image", type=str, required=True, help="Input RGB image")
    cmd_render.add_argument("--depth", type=str, required=True, help="Input depth map")
    cmd_render.add_argument("--lens", type=str, default="60 LPI Standard 3D", help="Lens profile name")
    cmd_render.add_argument("--printer", type=str, default="Generic UV Flatbed 720", help="Printer profile name")
    cmd_render.add_argument("--width", type=float, default=150.0, help="Print width in mm")
    cmd_render.add_argument("--height", type=float, default=100.0, help="Print height in mm")
    cmd_render.add_argument("--views", type=int, default=None, help="Force specific view count (None=auto)")
    cmd_render.add_argument("--strength", type=str, default="balanced", help="natural, balanced, strong, extreme")
    cmd_render.add_argument("--zpp-mode", type=str, default="surface", help="surface, front, behind")
    cmd_render.add_argument("--offset-mm", type=float, default=0.0, help="Phase offset in mm")
    cmd_render.add_argument("--skew-deg", type=float, default=0.0, help="Skew tilt in degrees")
    cmd_render.add_argument("--name", type=str, default="lenticular_job", help="Job name")
    cmd_render.add_argument("--outdir", type=str, default="outputs", help="Output directory")

    args = parser.parse_args()
    
    if args.command == "pitch-test":
        print(f"Generating Pitch Test Pattern: {args.lpi} LPI, {args.ppi} PPI...")
        generate_pitch_test_pattern(
            nominal_lpi=args.lpi,
            output_ppi=args.ppi,
            print_width_mm=args.width,
            print_height_mm=args.height,
            lpi_range=args.range,
            lpi_step=args.step,
            viewing_distance_mm=args.dist,
            output_path=args.output,
        )
        print(f"[OK] Saved pitch test pattern to: {args.output}")
        
    elif args.command == "analyze":
        img = load_image(args.image, mode="rgb")
        d = load_image(args.depth, mode="gray")
        analyzer = SceneAnalyzer(target_lens_lpi=args.lpi, output_ppi=args.ppi)
        report = analyzer.analyze(img, d.astype(float) / 255.0)
        print("\n" + "="*55)
        print("          LENTICULAR 2 SCENE ANALYSIS")
        print("="*55)
        print(f"Subject Coverage: {report.subject_coverage_pct:.1f}%")
        print(f"Subject Depth: {report.subject_depth_mean:.2f} | Background: {report.background_depth_mean:.2f}")
        print(f"Negative Space Ratio: {report.negative_space_ratio*100:.1f}%")
        print(f"Edge Jump Intensity: {report.edge_jump_intensity:.2f}")
        print(f"Recommended Camera Angle: +/-{report.recommended_angle_deg:.2f} deg")
        print(f"Recommended ZPP Mode: {report.recommended_zpp_mode} (ZPP Depth: {report.recommended_zpp_depth:.2f})")
        print(f"Recommended Views: {report.recommended_views}")
        print("\nRecommendations:")
        for r in report.recommendations:
            print(f"  * {r}")
        if report.warnings:
            print("\nWarnings:")
            for w in report.warnings:
                print(f"  [WARN] {w}")
        print("="*55 + "\n")
        
    elif args.command == "render":
        lens_profiles = load_lens_profiles()
        printer_profiles = load_printer_profiles()
        
        if args.lens not in lens_profiles:
            print(f"[ERROR] Lens '{args.lens}' not found. Available: {list(lens_profiles.keys())}")
            sys.exit(1)
        if args.printer not in printer_profiles:
            print(f"[ERROR] Printer '{args.printer}' not found. Available: {list(printer_profiles.keys())}")
            sys.exit(1)
            
        lens = lens_profiles[args.lens]
        printer = printer_profiles[args.printer]
        
        pipeline = ProductionPipeline(lens, printer, output_dir=args.outdir)
        results = pipeline.run(
            image_path=args.image,
            depth_path=args.depth,
            print_width_mm=args.width,
            print_height_mm=args.height,
            effect_strength=args.strength,
            zpp_mode=args.zpp_mode,
            view_count=args.views,
            registration_offset_mm=args.offset_mm,
            skew_degrees=args.skew_deg,
            job_name=args.name,
        )
        print("\n" + results["plan_summary"])
        print(f"\n[OK] Production Complete:")
        print(f"  * Interlaced TIFF: {results['interlaced_path']}")
        print(f"  * Preview GIF:     {results['preview_animation_path']}")
        print(f"  * JSON Report:     {results['report_path']}")


if __name__ == "__main__":
    main()
