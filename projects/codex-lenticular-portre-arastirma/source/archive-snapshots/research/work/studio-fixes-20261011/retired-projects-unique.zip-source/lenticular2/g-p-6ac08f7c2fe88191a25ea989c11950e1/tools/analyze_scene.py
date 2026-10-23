"""CLI tool to deeply analyze an image before lenticular 3D rendering and printing."""
import argparse
import json
from pathlib import Path
import sys

from PIL import Image

# Ensure project root is in path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from lenticular.analyzer import analyze_scene, generate_diagnostic_sheet, optimize_depth_map


def main():
    parser = argparse.ArgumentParser(description="Lenticular Akıllı Sahne ve Derinlik Analiz Motoru")
    parser.add_argument("--photo", required=True, help="Kaynak fotoğraf dosyasının yolu")
    parser.add_argument("--depth", default=None, help="Hazır derinlik haritası (isteğe bağlı; verilmezse AI ile tahmin edilir)")
    parser.add_argument("--output", default="outputs/analysis", help="Çıktı klasörü")
    parser.add_argument("--optimize-depth", action="store_true", help="Analiz önerilerine göre derinliği otomatik optimize et")
    args = parser.parse_args()

    photo_path = Path(args.photo).resolve()
    if not photo_path.is_file():
        print(f"HATA: Fotoğraf bulunamadı: {photo_path}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Görsel analiz ediliyor: {photo_path.name}")
    photo = Image.open(photo_path).convert("RGB")
    
    depth_arg = Path(args.depth).resolve() if args.depth else None
    analysis, depth, gap_mask, high_freq_mask = analyze_scene(photo, depth_arg)

    # Save JSON report
    report_file = output_dir / "scene_analysis.json"
    report_file.write_text(json.dumps(analysis, indent=2, ensure_ascii=False), encoding="utf-8")

    # Generate diagnostic sheet
    sheet_file = output_dir / "scene_analysis.png"
    generate_diagnostic_sheet(photo, depth, analysis, sheet_file)

    # Save recommended config
    rec_config = {
        "nr": analysis["calculated_recommendations"]["recommended_nr"],
        "angle_deg": analysis["calculated_recommendations"]["angle_deg"],
        "zero_reference": analysis["calculated_recommendations"]["zero_reference"],
        "reference_point": analysis["calculated_recommendations"]["reference_point"],
        "effect_strength": analysis["calculated_recommendations"]["effect_strength"],
        "front_strength": analysis["calculated_recommendations"]["front_strength"],
        "back_strength": analysis["calculated_recommendations"]["back_strength"],
        "depth_curve": analysis["calculated_recommendations"]["depth_curve"],
        "depth_smoothing": analysis["calculated_recommendations"]["depth_smoothing"],
        "edge_refinement": analysis["calculated_recommendations"]["edge_refinement"],
        "depth_black": analysis["calculated_recommendations"]["depth_black"],
        "depth_white": analysis["calculated_recommendations"]["depth_white"],
        "depth_gamma": analysis["calculated_recommendations"]["depth_gamma"],
        "max_parallax_percent": analysis["calculated_recommendations"]["max_parallax_percent"],
        "parallax_guard": analysis["calculated_recommendations"]["parallax_guard"],
        "edge_guard": analysis["calculated_recommendations"]["edge_guard"],
        "repair": True,
        "repair_quality": "advanced"
    }
    config_file = output_dir / "recommended_render.json"
    config_file.write_text(json.dumps(rec_config, indent=2, ensure_ascii=False), encoding="utf-8")

    # Optionally optimize depth
    if args.optimize_depth:
        print("[*] Derinlik haritası analiz bulgularına göre optimize ediliyor...")
        opt_depth = optimize_depth_map(photo, depth, analysis)
        from PIL import Image as PILImage
        import numpy as np
        opt_img = PILImage.fromarray((opt_depth * 255).astype(np.uint8))
        opt_img.save(output_dir / "optimized_depth.png")
        np.save(output_dir / "optimized_depth.npy", opt_depth)
        print(f"[+] Optimize edilmiş derinlik kaydedildi: {output_dir / 'optimized_depth.png'}")

    recs = analysis["calculated_recommendations"]
    print("\n" + "="*70)
    print(" LENTICULAR AKILLI GÖRSEL ANALİZ VE HESAPLAMA SONUÇLARI")
    print("="*70)
    print(f"Çözünürlük ve Yön: {analysis['image']['width']}x{analysis['image']['height']} ({analysis['image']['orientation']})")
    print(f"Ana Konu Alanı   : %{analysis['subject']['area_percentage']} | Merkez: {analysis['subject']['centroid']}")
    print(f"Tespit Edilen Boşluk / Negatif Alan: {analysis['negative_spaces_and_gaps']['total_detected_gaps']} adet")
    print(f"İnce Kenar / Saç Yoğunluğu: %{analysis['details_and_edges']['high_frequency_detail_percentage']}")
    print(f"Risk Değerlendirmesi: {analysis['risk_assessment']['level']}")
    print("-" * 70)
    print(" MATEMATİKSEL OLARAK HESAPLANAN EN UYGUN PARAMETRELER:")
    print(f" • Önerilen Kamera Açısı   : {recs['angle_deg']}° (Yırtılma ve çift görmeyi önleyen optimum açı)")
    print(f" • Sabit Sıfır Paralaks    : {recs['zero_reference']} (Konum: X={recs['reference_point']['x']}, Y={recs['reference_point']['y']})")
    print(f" • Ön / Arka Derinlik Gücü : Ön={recs['front_strength']}x | Arka={recs['back_strength']}x")
    print(f" • Derinlik Eğrisi / Koruma: {recs['depth_curve']} | Max Paralaks: %{recs['max_parallax_percent']}")
    print(f" • Dinamik Aralık Sınırları: Siyah={recs['depth_black']} | Beyaz={recs['depth_white']} | Gamma={recs['depth_gamma']}")
    print(f" • Önerilen Görünüş Sayısı : Nr={recs['recommended_nr']}")
    print("="*70)
    print(f"[+] Analiz Raporu : {report_file}")
    print(f"[+] Görsel Pano   : {sheet_file}")
    print(f"[+] Hazır Ayar    : {config_file}")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
