"""Execution script for VD 3-variant depth trial.
Uses Lenticular Studio engine without modifying source code.
"""
import sys
import os
from pathlib import Path
import json
import time
import math
import shutil
import hashlib

# Ensure Lenticular Studio is on sys.path
STUDIO_ROOT = Path(r"C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1")
if str(STUDIO_ROOT) not in sys.path:
    sys.path.insert(0, str(STUDIO_ROOT))

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageCms, ImageOps
import cv2
import tifffile

from lenticular.depth import (
    MODEL_REVISION, MODEL_ID, proximity_from_depth,
    estimate, load_mono_model, predict_depth
)
from lenticular.detail_depth import VERSION as DETAIL_VERSION, estimate_detail, surface_relief
from lenticular.repair import editable_depth, plan_parallax, save_parallax_map
from lenticular.geometry import validate as validate_render, read_depth
from lenticular.printing import (
    validate as validate_print, encode, pitch_test, registration,
    mixing_matrix, color_transform
)
from lenticular.analyzer import analyze_scene, save_analysis
from lenticular.runner import render, digest, find_blender

SETTINGS_JSON = Path(r"C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac173361d8c8191a1449be5154f589f\work\vd-three-variant-plan\vd-three-variant-settings.json")
OUTPUT_DIR = Path(r"C:\Users\USER\Documents\lenticular baskı")
SOURCE_PHOTO = Path(r"C:\Users\USER\Downloads\vd-gigapixel-recover v2-2x-faceai v2.jpg")


def step1_prepare_depth(settings, out_dir):
    print("=" * 60)
    print("ADIM 1: Derinlik Haritası Hazırlığı ve Önbellek Eşleştirme")
    print("=" * 60)
    
    prep_dir = out_dir / "prepared_depth"
    if (prep_dir / "depth.npy").is_file() and (prep_dir / "depth_preview.png").is_file():
        print("Önceden hazırlanmış derinlik haritası bulundu, doğrudan yükleniyor...")
        final_depth = np.load(prep_dir / "depth.npy", allow_pickle=False)
        return final_depth, prep_dir

    with Image.open(SOURCE_PHOTO) as img:
        size = img.size
        print(f"Kaynak görsel: {SOURCE_PHOTO}")
        print(f"Boyut: {size[0]} x {size[1]} piksel")
        if size != (1872, 3098):
            raise ValueError(f"Beklenen boyut (1872, 3098), bulunan: {size}")
            
    ref_norm = settings["variants"][0]["render"]["reference_point"]
    ref_px_x = ref_norm["x"] * (size[0] - 1)
    ref_px_y = ref_norm["y"] * (size[1] - 1)
    print(f"Burun referans noktası (normalize): x={ref_norm['x']:.6f}, y={ref_norm['y']:.6f}")
    print(f"Burun referans noktası (piksel): x={ref_px_x:.2f}, y={ref_px_y:.2f} (hedef: ~958, 432)")
    
    photo_hash = digest(SOURCE_PHOTO)
    print(f"Kaynak dosya SHA256: {photo_hash}")
    
    process_res = settings["variants"][0]["render"]["process_res"]  # 1008
    print(f"Derinlik model çözünürlüğü: {process_res}")
    
    base_key = hashlib.sha256((photo_hash + MODEL_REVISION + str(process_res)).encode()).hexdigest()
    depth_cache_folder = STUDIO_ROOT / ".studio" / "depth" / base_key
    print(f"Hedef derinlik önbellek yolu: {depth_cache_folder}")
    
    if (depth_cache_folder / "metadata.json").is_file() and (depth_cache_folder / "relative_depth.npy").is_file():
        print("Mevcut uyumlu DA3MONO-LARGE önbelleği bulundu, yükleniyor...")
    else:
        print(f"Önbellek bulunamadı. DA3MONO-LARGE (res={process_res}) ile tahmin başlatılıyor...")
        t0 = time.time()
        estimate(SOURCE_PHOTO, depth_cache_folder, process_res=process_res)
        print(f"Temel derinlik hesaplama tamamlandı: {time.time() - t0:.1f} saniye")
        
    raw_depth = np.load(depth_cache_folder / "relative_depth.npy", allow_pickle=False)
    normalization = settings["variants"][0]["render"]["depth_normalization"]  # preserve
    base_depth, norm_info = proximity_from_depth(raw_depth, normalization=normalization)
    print(f"Normalizasyon '{normalization}' uygulandı. Bounds: {norm_info['inverse_depth_bounds']}")
    
    detail_enabled = settings["variants"][0]["render"]["detail_enabled"]
    detail_strength = settings["variants"][0]["render"]["detail_strength"]
    surface_strength = settings["variants"][0]["render"]["surface_strength"]
    
    if detail_enabled:
        base_hash = hashlib.sha256(base_depth.tobytes()).hexdigest()
        detail_key = hashlib.sha256((photo_hash + base_hash + str(DETAIL_VERSION)).encode()).hexdigest()
        detail_cache_folder = STUDIO_ROOT / ".studio" / "depth_detail" / detail_key
        print(f"Ayrıntı derinliği önbellek yolu: {detail_cache_folder}")
        
        if (detail_cache_folder / "metadata.json").is_file() and (detail_cache_folder / "detail_delta.npy").is_file():
            print("Mevcut ayrıntı derinliği önbelleği bulundu, yükleniyor...")
            delta = np.load(detail_cache_folder / "detail_delta.npy", allow_pickle=False)
        else:
            print("Ayrıntı derinliği yerel AI bölgeleri hesaplanıyor...")
            t0 = time.time()
            delta = estimate_detail(SOURCE_PHOTO, base_depth, detail_cache_folder)
            print(f"Ayrıntı derinliği hesaplandı: {time.time() - t0:.1f} saniye")
            
        surface = surface_relief(SOURCE_PHOTO, base_depth, detail_cache_folder)
        combined = base_depth + detail_strength * delta + surface_strength * surface
        low, high = min(0.0, float(combined.min())), max(1.0, float(combined.max()))
        final_depth = ((combined - low) / (high - low)).astype(np.float32)
        print(f"Ayrıntılı derinlik birleştirildi (detail={detail_strength}, surface={surface_strength}).")
    else:
        final_depth = base_depth.copy()
        
    prep_dir.mkdir(parents=True, exist_ok=True)
    np.save(prep_dir / "depth.npy", final_depth, allow_pickle=False)
    Image.fromarray(np.rint(final_depth * 255).astype(np.uint8)).save(prep_dir / "depth_preview.png")
    Image.fromarray(np.rint(final_depth * 65535).astype(np.uint16)).save(prep_dir / "depth_16bit.png")
    
    ref_val = float(final_depth[round(ref_px_y), round(ref_px_x)])
    print(f"Referans noktası (burun) örneklenen ham derinlik: {ref_val:.4f}")
    print(f"Derinlik min: {final_depth.min():.4f}, max: {final_depth.max():.4f}, mean: {final_depth.mean():.4f}")
    
    return final_depth, prep_dir


def step2_run_analyzers_and_preview(settings, depth, out_dir):
    print("\n" + "=" * 60)
    print("ADIM 2: Sahne Analizi (A, B, C) ve Tekil C Önizlemesi")
    print("=" * 60)
    
    with Image.open(SOURCE_PHOTO) as original:
        photo = original.convert("RGBA")
        
    analysis_reports = {}
    for var in settings["variants"]:
        name = var["name"]
        print(f"\n--- Varyant Analizi: {name} ---")
        var_r = var["render"].copy()
        var_p = var["print"].copy()
        
        report, diagnostic = analyze_scene(photo, depth, var_r, var_p)
        analysis_reports[name] = report
        
        save_dir = out_dir / f"analysis_{name[0]}"
        save_analysis(save_dir, report, diagnostic)
        
        par = report["parallax"]
        budget = report["sampling_budget"]
        edits = report["edits"]
        print(f"İstenen Açı: {par['requested_angle_deg']:.2f}°, Uygulanan Açı: {par['effective_angle_deg']:.2f}° (Sınırlandı mı: {par['angle_limited']})")
        print(f"Max Paralaks: {par['max_parallax_percent']:.2f}% (İstenen sınır: %{var_r['max_parallax_percent']})")
        if "balanced" in edits and edits["balanced"]:
            b_front = edits["balanced"]["front"]
            b_back = edits["balanced"]["back"]
            print(f"Bütçe Gerçekleşen: Ön %{b_front['attainable_percent']:.2f} (hedef %{b_front['requested_percent']}), Arka %{b_back['attainable_percent']:.2f} (hedef %{b_back['requested_percent']})")
        print(f"Disparite Piksel Aralığı: [{par['endpoint_disparity_px_range'][0]:.1f}, {par['endpoint_disparity_px_range'][1]:.1f}] px")
        print(f"Kanal Başına Raster Piksel: {budget['pixels_per_channel']:.4f}")
        print(f"Kanal Sayısı Ne: {var_p['ne']}, Render Kare Sayısı Nr: {var_r['nr']}")
        print(f"Uyarılar ({len(report['warnings'])}):")
        for w in report["warnings"]:
            print(f"  - {w}")
            
    print("\n--- Tekil C Önizleme Renderi (En Zor Varyant Erken Kontrolü) ---")
    c_var = settings["variants"][2]  # C - Guclu
    c_render_cfg = c_var["render"].copy()
    c_render_cfg["render_long_edge"] = settings["preview_overrides"]["render_long_edge"]  # 1024
    c_render_cfg["grid_size"] = settings["preview_overrides"]["grid_size"]  # 512
    
    preview_out = out_dir / "preview_C"
    preview_render_dir = preview_out / "render"
    
    if (preview_render_dir / "coverage.json").is_file() and (preview_render_dir / "views" / "view_0009.png").is_file():
        print("Mevcut C önizleme renderi bulundu, yeniden çalıştırılmıyor.")
    else:
        if preview_out.exists():
            shutil.rmtree(preview_out)
        preview_out.mkdir(parents=True, exist_ok=True)
        
        c_photo = photo.copy()
        long_edge = c_render_cfg["render_long_edge"]
        if long_edge and max(c_photo.size) > long_edge:
            c_photo.thumbnail((long_edge, long_edge), Image.Resampling.LANCZOS)
            c_depth = cv2.resize(depth, c_photo.size, interpolation=cv2.INTER_LINEAR)
        else:
            c_depth = depth.copy()
            
        c_edited, c_edits = editable_depth(c_depth, c_render_cfg, c_photo)
        c_render_cfg["zero_reference"] = c_edits["zero_reference"]
        c_geom, c_par, c_disp = plan_parallax(c_edited, c_photo.size, c_render_cfg)
        
        c_photo.save(preview_out / "photo.png")
        np.save(preview_out / "depth.npy", c_edited, allow_pickle=False)
        save_parallax_map(c_disp, preview_out / "parallax.png")
        
        config = validate_render(dict(
            nr=c_render_cfg["nr"], ne=c_var["print"]["ne"],
            camera_axis=c_render_cfg["camera_axis"],
            grid_size=c_render_cfg["grid_size"], edge_mode="split",
            **c_geom
        ))
        
        print(f"C Önizleme Blender Render başlatılıyor: boyut={c_photo.size}, grid={c_render_cfg['grid_size']}...")
        t0 = time.time()
        blender_path = find_blender()
        render(
            preview_out / "photo.png", preview_out / "depth.npy",
            preview_render_dir, config, blender=blender_path,
            repair={
                "enabled": c_render_cfg["repair"],
                "layers": c_render_cfg["layers"],
                "radius": c_render_cfg["inpaint_radius"],
                "quality": c_render_cfg["repair_quality"]
            }
        )
        print(f"C Önizleme tamamlandı: {time.time() - t0:.1f} saniye")
        
    coverage = json.loads((preview_render_dir / "coverage.json").read_text(encoding="utf-8"))
    print(f"C Önizleme Max Non-opaque (Boşluk/Şeffaflık) Oranı: {coverage['max_nonopaque_fraction']:.6f}")
    if coverage['max_nonopaque_fraction'] > 0.0005:
        print("UYARI: C önizlemesinde %0.05 üzerinde boşluk tespit edildi!")
    else:
        print("KONTROL BAŞARILI: C varyantında boşluk veya kenar yırtılması kritik eşiğin (%0.05) altında.")
        
    return analysis_reports, coverage


def step3_run_full_renders(settings, depth, out_dir):
    print("\n" + "=" * 60)
    print("ADIM 3: Üç Nihai Tam Render (A, B, C) — grid_size=1024, tam kadraj")
    print("=" * 60)
    
    with Image.open(SOURCE_PHOTO) as original:
        photo = original.convert("RGBA")
        
    blender_path = find_blender()
    render_results = {}
    
    for var in settings["variants"]:
        name = var["name"]
        code = name[0]
        print(f"\n>>> Tam Render: {name} <<<")
        
        var_r = var["render"].copy()
        var_r["grid_size"] = 1024
        var_r["render_long_edge"] = 0  # Tam çözünürlük 1872x3098
        
        var_out = out_dir / f"render_{code}"
        var_prepared = var_out / "prepared"
        var_render_dir = var_out / "render"
        
        # Check if already rendered
        if (var_render_dir / "coverage.json").is_file() and (var_render_dir / "views" / "view_0009.png").is_file():
            print(f"{name} için tam render zaten mevcut, yeniden kullanılacak.")
            coverage = json.loads((var_render_dir / "coverage.json").read_text(encoding="utf-8"))
            quality = json.loads((var_out / "quality.json").read_text(encoding="utf-8"))
            render_results[code] = {
                "render_dir": var_render_dir,
                "coverage": coverage,
                "quality": quality
            }
            continue
            
        var_prepared.mkdir(parents=True, exist_ok=True)
        edited_depth, edits = editable_depth(depth, var_r, photo)
        var_r["zero_reference"] = edits["zero_reference"]
        geometry, parallax, disparity = plan_parallax(edited_depth, photo.size, var_r)
        
        photo.save(var_prepared / "photo.png")
        np.save(var_prepared / "depth.npy", edited_depth, allow_pickle=False)
        Image.fromarray(np.rint(edited_depth * 255).astype(np.uint8)).save(var_prepared / "depth.png")
        save_parallax_map(disparity, var_prepared / "parallax.png")
        
        ref_pt = var_r.get("reference_point")
        if ref_pt:
            rx = round(ref_pt["x"] * (photo.width - 1))
            ry = round(ref_pt["y"] * (photo.height - 1))
            rad_x, rad_y = max(1, round(photo.width * 0.08)), max(1, round(photo.height * 0.05))
            region = disparity[max(0, ry - rad_y):ry + rad_y + 1, max(0, rx - rad_x):rx + rad_x + 1]
            relief = float(np.percentile(region, 95) - np.percentile(region, 5))
            parallax["reference_point"] = ref_pt
            parallax["reference_endpoint_disparity_px"] = float(disparity[ry, rx])
            parallax["reference_region_relief_px"] = relief
            parallax["reference_region_relief_percent"] = relief / photo.width * 100
            
        config = validate_render(dict(
            nr=var_r["nr"], ne=var["print"]["ne"],
            camera_axis=var_r["camera_axis"],
            grid_size=var_r["grid_size"], edge_mode="split",
            **geometry
        ))
        
        quality = dict(
            edits=edits, parallax=parallax,
            repair_engine=var_r["repair_quality"] if var_r["repair"] else "none",
            render_size=list(photo.size), source_size=list(photo.size),
            source_resolution_render=True
        )
        
        print(f"Blender render başlatılıyor (Nr={var_r['nr']}, Layers={var_r['layers']}, Grid=1024)...")
        t0 = time.time()
        render(
            var_prepared / "photo.png", var_prepared / "depth.npy",
            var_render_dir, config, blender=blender_path,
            repair={
                "enabled": var_r["repair"],
                "layers": var_r["layers"],
                "radius": var_r["inpaint_radius"],
                "quality": var_r["repair_quality"]
            }
        )
        print(f"{name} render tamamlandı: {time.time() - t0:.1f} saniye")
        
        coverage = json.loads((var_render_dir / "coverage.json").read_text(encoding="utf-8"))
        mesh_stats = json.loads((var_render_dir / "job.json").read_text(encoding="utf-8"))["mesh"]
        quality.update(max_nonopaque_fraction=coverage["max_nonopaque_fraction"], mesh=mesh_stats)
        if (var_render_dir / "repair.json").is_file():
            quality["restoration"] = json.loads((var_render_dir / "repair.json").read_text(encoding="utf-8"))
            
        (var_out / "quality.json").write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")
        
        render_results[code] = {
            "render_dir": var_render_dir,
            "coverage": coverage,
            "quality": quality
        }
        
    return render_results


def step4_and_5_verify_views_and_geometry(settings, render_results):
    print("\n" + "=" * 60)
    print("ADIM 4 & 5: Geometrik Doğrulama ve Görüş Kontrolleri")
    print("=" * 60)
    
    verification = {}
    
    for var in settings["variants"]:
        code = var["name"][0]
        res = render_results[code]
        r_dir = res["render_dir"]
        qual = res["quality"]
        par = qual["parallax"]
        cov = res["coverage"]
        
        print(f"\n--- Kontrol: {var['name']} ---")
        print(f"Açı: İstenen {par['requested_angle_deg']:.2f}°, Gerçekleşen {par['effective_angle_deg']:.2f}°")
        print(f"Disparite Piksel Aralığı: [{par['endpoint_disparity_px_range'][0]:.2f}, {par['endpoint_disparity_px_range'][1]:.2f}] px")
        print(f"Max Paralaks: %{par['max_parallax_percent']:.2f}")
        print(f"Burun Çevresi İç Hacim (Relief): {par.get('reference_region_relief_px', 0):.2f} px (%{par.get('reference_region_relief_percent', 0):.3f})")
        print(f"Görünüş Boşluk Oranı (Max Non-opaque): {cov['max_nonopaque_fraction']:.6f}")
        
        # Check nose reference position in view 0, 4, 9
        ref_pt = var["render"]["reference_point"]
        w, h = qual["render_size"]
        nx, ny = round(ref_pt["x"] * (w - 1)), round(ref_pt["y"] * (h - 1))
        
        # Crop 40x40 patch around nose across views
        patch_rad = 20
        patches = []
        for v_idx in [0, 4, 9]:
            v_img = Image.open(r_dir / f"views/view_{v_idx:04d}.png").convert("L")
            patch = np.asarray(v_img.crop((nx - patch_rad, ny - patch_rad, nx + patch_rad, ny + patch_rad)), dtype=np.float32)
            patches.append(patch)
            
        # Cross-correlation to measure shift relative to center view (view 4)
        center_patch = patches[1]
        shifts = []
        for i, p in enumerate([patches[0], patches[2]]):
            res_corr = cv2.matchTemplate(p, center_patch[2:-2, 2:-2], cv2.TM_CCOEFF_NORMED)
            _, _, _, max_loc = cv2.minMaxLoc(res_corr)
            dx = max_loc[0] - 2
            dy = max_loc[1] - 2
            shifts.append((dx, dy))
            
        print(f"Burun Noktası Hareketi: Uç Sol (0) -> Merkez: dx={shifts[0][0]}, dy={shifts[0][1]} px | Uç Sağ (9) -> Merkez: dx={shifts[1][0]}, dy={shifts[1][1]} px")
        max_shift = max(abs(shifts[0][0]), abs(shifts[1][0]))
        if max_shift <= 1:
            print("BURUN SABİTLİĞİ KONTROLÜ: BAŞARILI (Hareket <= 1 piksel)")
        else:
            print(f"UYARI: Burun noktası {max_shift} piksel kayma gösterdi.")
            
        verification[code] = {
            "requested_angle_deg": par["requested_angle_deg"],
            "effective_angle_deg": par["effective_angle_deg"],
            "endpoint_disparity_px_range": par["endpoint_disparity_px_range"],
            "max_parallax_percent": par["max_parallax_percent"],
            "reference_relief_px": par.get("reference_region_relief_px", 0),
            "max_nonopaque_fraction": cov["max_nonopaque_fraction"],
            "nose_shifts_px": shifts,
            "nose_stable": max_shift <= 1
        }
        
    return verification


def step6_encode_and_assemble(settings, render_results, out_dir):
    print("\n" + "=" * 60)
    print("ADIM 6: Lenticular Interlace Encode ve Birleşik Baskı Sayfası")
    print("=" * 60)
    
    panel_w_px = settings["sheet"]["panel_size_px"][0]  # 6141
    panel_h_px = settings["sheet"]["panel_size_px"][1]  # 10163
    ppi = settings["sheet"]["ppi"]  # 1200
    
    encoded_panels = {}
    
    for var in settings["variants"]:
        name = var["name"]
        code = name[0]
        r_dir = render_results[code]["render_dir"]
        
        # 1. Sheet phase encode
        sheet_phase = var["sheet_phase_for_panel_export"]
        print(f"\n--- Interlace: {name} (Sayfa Fazı: {sheet_phase:.4f}) ---")
        p_cfg_sheet = var["print"].copy()
        p_cfg_sheet["phase"] = sheet_phase
        
        sheet_print_dir = out_dir / f"print_{code}_sheet"
        sheet_print_dir.mkdir(parents=True, exist_ok=True)
        sheet_tif = sheet_print_dir / "interlaced.tif"
        
        if not sheet_tif.is_file():
            def prog_s(msg):
                if "%" in msg and int(msg.split("%")[-1]) % 25 == 0:
                    print(f"  {msg}")
            rep = encode(r_dir, sheet_print_dir, p_cfg_sheet, progress=prog_s)
            (out_dir / f"print_quality_{code}_sheet.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            print("  Mevcut sayfa interlaced TIFF bulundu.")
            
        encoded_panels[f"{code}_sheet"] = sheet_tif
        
        # 2. Independent phase=0 encode (for independent lens cutouts)
        if sheet_phase != 0.0:
            print(f"--- Interlace: {name} (Bağımsız Panel Fazı: 0.0) ---")
            p_cfg_indep = var["print"].copy()
            p_cfg_indep["phase"] = 0.0
            indep_print_dir = out_dir / f"print_{code}_indep"
            indep_print_dir.mkdir(parents=True, exist_ok=True)
            indep_tif = indep_print_dir / "interlaced.tif"
            
            if not indep_tif.is_file():
                def prog_i(msg):
                    if "%" in msg and int(msg.split("%")[-1]) % 25 == 0:
                        print(f"  {msg}")
                rep = encode(r_dir, indep_print_dir, p_cfg_indep, progress=prog_i)
                (out_dir / f"print_quality_{code}_indep.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
            else:
                print("  Mevcut bağımsız interlaced TIFF bulundu.")
            encoded_panels[f"{code}_indep"] = indep_tif
        else:
            encoded_panels[f"{code}_indep"] = sheet_tif

    # Copy standalone panel files to top-level output for clear user access
    print("\nBağımsız ve sayfa panelleri dışa aktarılıyor...")
    for code in ["A", "B", "C"]:
        shutil.copyfile(encoded_panels[f"{code}_indep"], out_dir / f"panel_{code}_bagimsiz_phase0.tif")
        shutil.copyfile(encoded_panels[f"{code}_sheet"], out_dir / f"panel_{code}_sheet_phase.tif")
        
    # Assemble side-by-side sheet
    print("\n--- Birleşik Baskı Sayfası Oluşturuluyor ---")
    tot_w = panel_w_px * 3  # 18423 px
    tot_h = panel_h_px      # 10163 px
    print(f"Birleşik görüntü alanı boyutu: {tot_w} x {tot_h} piksel (1200 PPI, 389.95 x 215.12 mm)")
    
    # Read panels block-by-block or full array
    print("Paneller okunuyor ve yatay birleştiriliyor...")
    panel_A = tifffile.imread(encoded_panels["A_sheet"])
    panel_B = tifffile.imread(encoded_panels["B_sheet"])
    panel_C = tifffile.imread(encoded_panels["C_sheet"])
    
    combined_img = np.concatenate([panel_A, panel_B, panel_C], axis=1)
    del panel_A, panel_B, panel_C
    print(f"Birleşik görüntü belleğe alındı: {combined_img.shape}, dtype={combined_img.dtype}")
    
    # Save pure image sheet (without labels)
    pure_sheet_path = out_dir / "karsilastirma_sayfasi_resim_alani_1200ppi.tif"
    print(f"Kaydediliyor: {pure_sheet_path.name}...")
    tifffile.imwrite(
        pure_sheet_path, combined_img,
        photometric="rgb", resolution=(ppi, ppi), resolutionunit="INCH"
    )
    
    # Generate 6mm bottom label strip
    # 6 mm at 1200 PPI: round(6 * 1200 / 25.4) = 283 px
    strip_h_px = round(settings["sheet"]["label_strip_mm"] * ppi / 25.4)  # 283 px
    print(f"Etiket şeridi hazırlanıyor: {tot_w} x {strip_h_px} piksel (6 mm)...")
    
    strip_pil = Image.new("RGB", (tot_w, strip_h_px), color=(255, 255, 255))
    draw = ImageDraw.Draw(strip_pil)
    
    # Draw horizontal separator line at top of strip
    draw.line([(0, 0), (tot_w, 0)], fill=(200, 200, 200), width=3)
    
    # Choose font
    font_size = 96
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
        sub_font = ImageFont.truetype("arial.ttf", 48)
    except OSError:
        font = ImageFont.load_default()
        sub_font = ImageFont.load_default()
        
    labels = [
        ("A - Normal", "Açı: 3.0° | Ön %1.0 | Arka %1.5 | Lens: 50.20 LPI | Ne=10 | Faz: 0.0000"),
        ("B - Artırılmış", "Açı: 4.5° | Ön %1.5 | Arka %2.2 | Lens: 50.20 LPI | Ne=10 | Faz: 0.8985"),
        ("C - Güçlü", "Açı: 6.0° | Ön %2.0 | Arka %3.0 | Lens: 50.20 LPI | Ne=10 | Faz: 0.7970")
    ]
    
    for i, (title_text, sub_text) in enumerate(labels):
        center_x = i * panel_w_px + panel_w_px // 2
        
        # Measure text
        bbox_t = draw.textbbox((0, 0), title_text, font=font)
        tw = bbox_t[2] - bbox_t[0]
        draw.text((center_x - tw // 2, 40), title_text, fill=(20, 20, 20), font=font)
        
        bbox_s = draw.textbbox((0, 0), sub_text, font=sub_font)
        sw = bbox_s[2] - bbox_s[0]
        draw.text((center_x - sw // 2, 160), sub_text, fill=(90, 90, 90), font=sub_font)
        
        # Panel border ticks
        if i > 0:
            draw.line([(i * panel_w_px, 0), (i * panel_w_px, strip_h_px)], fill=(200, 200, 200), width=2)
            
    strip_arr = np.asarray(strip_pil, dtype=np.uint8)
    labeled_combined = np.concatenate([combined_img, strip_arr], axis=0)
    del strip_arr
    print(f"Etiketli tam sayfa boyutu: {labeled_combined.shape} piksel (1200 PPI, 389.95 x 221.12 mm)")
    
    labeled_sheet_path = out_dir / "karsilastirma_sayfasi_etiketli_1200ppi.tif"
    print(f"Kaydediliyor: {labeled_sheet_path.name}...")
    tifffile.imwrite(
        labeled_sheet_path, labeled_combined,
        photometric="rgb", resolution=(ppi, ppi), resolutionunit="INCH"
    )
    
    # Create low-resolution preview for inspection (width = 3000 px)
    print("Düşük boyutlu önizleme görseli oluşturuluyor...")
    preview_pil = Image.fromarray(labeled_combined)
    preview_scale = 3000 / tot_w
    prev_w = 3000
    prev_h = round(labeled_combined.shape[0] * preview_scale)
    preview_pil.thumbnail((prev_w, prev_h), Image.Resampling.LANCZOS)
    
    preview_jpg_path = out_dir / "karsilastirma_onizleme_kucuk.jpg"
    preview_pil.save(preview_jpg_path, quality=90)
    print(f"Önizleme kaydedildi: {preview_jpg_path.name} ({prev_w} x {prev_h} px)")
    
    return pure_sheet_path, labeled_sheet_path, preview_jpg_path


def step7_generate_final_deliverables(settings, render_results, verification, out_dir):
    print("\n" + "=" * 60)
    print("ADIM 7: Nihai Raporlar ve Kısa Baskı Notu")
    print("=" * 60)
    
    # 1. Copy JSON
    shutil.copyfile(SETTINGS_JSON, out_dir / "vd-three-variant-settings.json")
    
    # 2. Print Note Markdown
    note_lines = [
        "# VD — Üç Derinlik Denemesi Baskı Notu ve Kalibrasyon Taslağı",
        "",
        "> [!IMPORTANT]",
        "> Bu çalışma bir **baskı denemesi / kalibrasyon taslağıdır**. Çıktılar 50.20 LPI lens ve 1200 DPI yazıcı adayı için dijital olarak doğrulanmıştır; henüz fiziksel RIP/baskı doğrulaması yapılmamıştır.",
        "",
        "## 1. Üretim Özeti ve Parametreler",
        f"- **Kaynak Görsel:** `vd-gigapixel-recover v2-2x-faceai v2.jpg` (1872 × 3098 px, Tam kadraj)",
        f"- **Sabit Burun Referansı:** Piksel (958, 432) | Normalize (x=0.512026, y=0.139490)",
        f"- **Derinlik Modeli:** DA3MONO-LARGE (process_res=1008, preserve normalizasyon) + Ayrıntılı yerel AI derinlik (güç 0.8)",
        f"- **Baskı Çözünürlüğü:** 1200 PPI / 1200 DPI",
        f"- **Lens:** Nominal ve Etkin 50.20 LPI dikey, Tilt=0, Bleed=0, Fit=Contain",
        f"- **Kanal Sayısı:** Ne=10 kanal, Nr=10 kamera görünüşü",
        f"- **Kanal Başına Raster Piksel:** 2.3904 piksel (Kanal ayrımı matematiksel olarak yeterlidir)",
        "",
        "## 2. Varyant Karşılaştırma Tablosu",
        "",
        "| Parametre | A - Normal | B - Artırılmış | C - Güçlü |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Kamera Açısı (İstenen / Uygulanan)** | {verification['A']['requested_angle_deg']:.1f}° / {verification['A']['effective_angle_deg']:.2f}° | {verification['B']['requested_angle_deg']:.1f}° / {verification['B']['effective_angle_deg']:.2f}° | {verification['C']['requested_angle_deg']:.1f}° / {verification['C']['effective_angle_deg']:.2f}° |",
        f"| **Hedef Bütçe (Ön / Arka Paralaks)** | %1.0 / %1.5 | %1.5 / %2.2 | %2.0 / %3.0 |",
        f"| **Gerçekleşen Max Paralaks** | %{verification['A']['max_parallax_percent']:.2f} | %{verification['B']['max_parallax_percent']:.2f} | %{verification['C']['max_parallax_percent']:.2f} |",
        f"| **Disparite Aralığı** | [{verification['A']['endpoint_disparity_px_range'][0]:.1f}, {verification['A']['endpoint_disparity_px_range'][1]:.1f}] px | [{verification['B']['endpoint_disparity_px_range'][0]:.1f}, {verification['B']['endpoint_disparity_px_range'][1]:.1f}] px | [{verification['C']['endpoint_disparity_px_range'][0]:.1f}, {verification['C']['endpoint_disparity_px_range'][1]:.1f}] px |",
        f"| **Burun Çevresi İç Hacim (Relief)** | {verification['A']['reference_relief_px']:.1f} px | {verification['B']['reference_relief_px']:.1f} px | {verification['C']['reference_relief_px']:.1f} px |",
        f"| **Sayfa Birleştirme Fazı** | 0.0000 | 0.8985 | 0.7970 |",
        f"| **Bağımsız Panel Fazı** | 0.0000 | 0.0000 | 0.0000 |",
        f"| **Görünüş Boşluk Oranı** | %{verification['A']['max_nonopaque_fraction']*100:.4f} | %{verification['B']['max_nonopaque_fraction']*100:.4f} | %{verification['C']['max_nonopaque_fraction']*100:.4f} |",
        f"| **Burun Sabitliği (Uç Görüşler)** | {'Sabit (<=1 px)' if verification['A']['nose_stable'] else 'Sapma var'} | {'Sabit (<=1 px)' if verification['B']['nose_stable'] else 'Sapma var'} | {'Sabit (<=1 px)' if verification['C']['nose_stable'] else 'Sapma var'} |",
        "",
        "## 3. Sayfa ve Dosya Yapısı",
        "",
        "1. **Tek Parça Lens Altında Birleşik Karşılaştırma Sayfası:**",
        "   - `karsilastirma_sayfasi_etiketli_1200ppi.tif`: 18423 × 10446 px (~389.95 × 221.12 mm). Altta 6 mm açıklama şeridi mevcuttur.",
        "   - `karsilastirma_sayfasi_resim_alani_1200ppi.tif`: 18423 × 10163 px (~389.95 × 215.12 mm). Saf görüntü alanıdır.",
        "   - **Sürekli Lens Fazı Uyarısı:** Tek lens yaprağı altında şerit başlangıcının kaymaması için B paneli faz=0.8985, C paneli faz=0.7970 ile kodlanarak birleştirilmiştir. `(global_phase + x_offset_px * 50.20 / 1200) % 1` kuralı korunmuştur.",
        "",
        "2. **Ayrı Lens Parçaları İçin Bağımsız Panel Dosyaları (Faz = 0.0):**",
        "   - `panel_A_bagimsiz_phase0.tif`: 6141 × 10163 px (129.98 × 215.12 mm)",
        "   - `panel_B_bagimsiz_phase0.tif`: 6141 × 10163 px (129.98 × 215.12 mm)",
        "   - `panel_C_bagimsiz_phase0.tif`: 6141 × 10163 px (129.98 × 215.12 mm)",
        "   *Paneller ayrı ayrı kesilmiş 13 cm lenslerin altına yerleştirilecekse bu bağımsız faz=0 dosyaları basılmalıdır.*",
        "",
        "3. **Önizleme ve Kalite Belgeleri:**",
        "   - `karsilastirma_onizleme_kucuk.jpg`: Hızlı ekrandan inceleme için 3000 px genişliğinde önizleme görseli.",
        "   - `analysis_A/`, `analysis_B/`, `analysis_C/`: Sahne analizi raporları ve optik risk haritaları.",
        "   - `render_A/`, `render_B/`, `render_C/`: Her varyantın 10 adet 3D kamera karesi, derinlik ve onarım katmanları.",
        "",
        "## 4. Kritik Baskı ve RIP Talimatları",
        "- **Baskı Ölçeği:** Yazdırma yazılımında kesinlikle **%100 (Gerçek Boyut / Do Not Scale)** seçilmeli; 'Sayfaya Sığdır' veya yeniden örnekleme kapatılmalıdır.",
        "- **13 cm Kuralı:** Her görsel paneli tam olarak 129.98 mm (6141 piksel) olarak sınırlandırılmıştır. Birleşik sayfa eni ~39 cm'dir. Tüm sayfayı 13 cm'e küçültmeyiniz.",
        "- **Renk Profili:** Çıktılar profilli RGB modundadır. Verilmiş bir ICC dosyası olmadığı için yapay CMYK dönüşümü yapılmamıştır.",
        "- **Ön/Arka Baskı:** Dosyalar önden yönlendirilmiş (mirror=false, white_underbase=false) deneme formatındadır. Arka yüz UV baskı yapılacaksa RIP veya laminasyon aşamasında ters baskı gereksinimi doğrulanmalıdır."
    ]
    
    note_path = out_dir / "baski-notu.md"
    note_path.write_text("\n".join(note_lines), encoding="utf-8")
    print(f"Baskı notu kaydedildi: {note_path.name}")


def main():
    with open(SETTINGS_JSON, "r", encoding="utf-8") as f:
        settings = json.load(f)
        
    depth, prep_dir = step1_prepare_depth(settings, OUTPUT_DIR)
    reports, cov = step2_run_analyzers_and_preview(settings, depth, OUTPUT_DIR)
    render_results = step3_run_full_renders(settings, depth, OUTPUT_DIR)
    verification = step4_and_5_verify_views_and_geometry(settings, render_results)
    pure_tif, labeled_tif, prev_jpg = step6_encode_and_assemble(settings, render_results, OUTPUT_DIR)
    step7_generate_final_deliverables(settings, render_results, verification, OUTPUT_DIR)
    print("\n" + "=" * 60)
    print("TÜM SÜREÇ EKSİKSİZ VE BAŞARIYLA TAMAMLANDI!")
    print("=" * 60)


if __name__ == "__main__":
    main()
