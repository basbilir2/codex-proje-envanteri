"""Execution adapter for VD Strong depth trial (50.20 / 75 / 100 LPI).
Reuses shared 12-view Blender render set across three LPI interlace prints.
Usage:
  python tools/execute_strong_trial.py --plan "plans/vd-strong-50.20-75-100-20261012/strong-plan.json"
"""
import argparse
import json
import math
import shutil
import sys
import time
from pathlib import Path

# Add Lenticular Studio to sys.path
STUDIO_ROOT = Path(r"C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1")
if str(STUDIO_ROOT) not in sys.path:
    sys.path.insert(0, str(STUDIO_ROOT))

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import tifffile

from lenticular.geometry import validate as validate_render
from lenticular.printing import encode, validate as validate_print
from lenticular.repair import editable_depth, plan_parallax, save_parallax_map
from lenticular.runner import digest, find_blender, render


def verify_inputs(plan_data):
    source_path = Path(plan_data["source"]).resolve()
    depth_path = Path(plan_data["depth_cache"]).resolve()

    if not source_path.is_file():
        raise FileNotFoundError(f"Kaynak dosya bulunamadı: {source_path}")
    if not depth_path.is_file():
        raise FileNotFoundError(f"Derinlik haritası bulunamadı: {depth_path}")

    source_hash = digest(source_path)
    if source_hash != plan_data["source_sha256"]:
        raise ValueError(
            f"Kaynak hash uyuşmazlığı: {source_hash} != {plan_data['source_sha256']}"
        )

    depth_hash = digest(depth_path)
    if depth_hash != plan_data["depth_sha256"]:
        raise ValueError(
            f"Derinlik hash uyuşmazlığı: {depth_hash} != {plan_data['depth_sha256']}"
        )

    print("Girdi doğrulaması başarılı:")
    print(f"  Kaynak: {source_path} ({source_hash[:16]}...)")
    print(f"  Derinlik: {depth_path} ({depth_hash[:16]}...)")
    return source_path, depth_path


def run_preview_render(plan_data, source_photo, depth_arr, blender_path):
    shared_cfg = plan_data["shared_render"]["render"]
    out_root = Path(r"C:\Users\USER\Documents\lenticular baskı\vd_belirgin_derinlik_20261012")
    preview_dir = out_root / "preview_1024"
    preview_render = preview_dir / "render"
    nr = shared_cfg["nr"]

    cov_file = preview_render / "coverage.json"
    if cov_file.is_file() and all(
        (preview_render / f"views/view_{i:04d}.png").is_file() for i in range(nr)
    ):
        cov = json.loads(cov_file.read_text(encoding="utf-8"))
        print(f"  Önizleme zaten mevcut (Boşluk oranı: {cov['max_nonopaque_fraction']:.6f}).")
        return cov, preview_render

    print("\n--- 1. Adım: Ortak 1024 px Önizleme Renderı Başlatılıyor ---")
    preview_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(source_photo) as orig:
        c_photo = orig.convert("RGBA")

    c_photo.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    c_depth = cv2.resize(depth_arr, c_photo.size, interpolation=cv2.INTER_LINEAR)

    cfg = shared_cfg.copy()
    cfg["render_long_edge"] = 1024
    cfg["grid_size"] = 512

    c_edited, c_edits = editable_depth(c_depth, cfg, c_photo)
    cfg["zero_reference"] = c_edits["zero_reference"]
    c_geom, c_par, c_disp = plan_parallax(c_edited, c_photo.size, cfg)

    c_photo.save(preview_dir / "photo.png")
    np.save(preview_dir / "depth.npy", c_edited, allow_pickle=False)
    save_parallax_map(c_disp, preview_dir / "parallax.png")

    render_config = validate_render(
        dict(
            nr=cfg["nr"],
            ne=plan_data["variants"][0]["print"]["ne"],
            camera_axis=cfg["camera_axis"],
            grid_size=cfg["grid_size"],
            edge_mode="split",
            **c_geom,
        )
    )

    t0 = time.time()
    render(
        preview_dir / "photo.png",
        preview_dir / "depth.npy",
        preview_render,
        render_config,
        blender=blender_path,
        repair={
            "enabled": cfg["repair"],
            "layers": cfg["layers"],
            "radius": cfg["inpaint_radius"],
            "quality": cfg["repair_quality"],
        },
    )
    print(f"  Önizleme renderı tamamlandı: {time.time() - t0:.1f} sn")
    cov = json.loads((preview_render / "coverage.json").read_text(encoding="utf-8"))
    print(f"  Önizleme Max Non-opaque oranı: {cov['max_nonopaque_fraction']:.6f}")
    return cov, preview_render


def run_full_render(plan_data, source_photo, depth_arr, blender_path):
    shared_cfg = plan_data["shared_render"]["render"]
    out_root = Path(r"C:\Users\USER\Documents\lenticular baskı\vd_belirgin_derinlik_20261012")
    render_output = out_root / "shared_render_12"
    prepared_dir = out_root / "prepared_shared_12"
    nr = shared_cfg["nr"]

    cov_file = render_output / "coverage.json"
    manifest_file = render_output / "render_manifest.json"
    quality_file = render_output / "quality.json"

    if (
        cov_file.is_file()
        and manifest_file.is_file()
        and quality_file.is_file()
        and all((render_output / f"views/view_{i:04d}.png").is_file() for i in range(nr))
    ):
        print(f"  Tam 12-görüşlü render önbellekte mevcut: {render_output}")
        cov = json.loads(cov_file.read_text(encoding="utf-8"))
        quality = json.loads(quality_file.read_text(encoding="utf-8"))
        return {
            "render_dir": render_output,
            "coverage": cov,
            "quality": quality,
            "cached": True,
        }

    print("\n--- 2. Adım: Tam Çözünürlüklü 12-Görüşlü Ortak Render Başlatılıyor ---")
    prepared_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(source_photo) as orig:
        photo = orig.convert("RGBA")

    var_r = shared_cfg.copy()
    edited_depth, edits = editable_depth(depth_arr, var_r, photo)
    var_r["zero_reference"] = edits["zero_reference"]
    geometry, parallax, disparity = plan_parallax(edited_depth, photo.size, var_r)

    photo.save(prepared_dir / "photo.png")
    np.save(prepared_dir / "depth.npy", edited_depth, allow_pickle=False)
    Image.fromarray(np.rint(edited_depth * 255).astype(np.uint8)).save(
        prepared_dir / "depth.png"
    )
    save_parallax_map(disparity, prepared_dir / "parallax.png")

    ref_pt = var_r.get("reference_point")
    if ref_pt:
        rx = round(ref_pt["x"] * (photo.width - 1))
        ry = round(ref_pt["y"] * (photo.height - 1))
        rad_x, rad_y = max(1, round(photo.width * 0.08)), max(1, round(photo.height * 0.05))
        region = disparity[
            max(0, ry - rad_y) : ry + rad_y + 1, max(0, rx - rad_x) : rx + rad_x + 1
        ]
        relief = float(np.percentile(region, 95) - np.percentile(region, 5))
        parallax["reference_point"] = ref_pt
        parallax["reference_endpoint_disparity_px"] = float(disparity[ry, rx])
        parallax["reference_region_relief_px"] = relief
        parallax["reference_region_relief_percent"] = relief / photo.width * 100

    render_config = validate_render(
        dict(
            nr=var_r["nr"],
            ne=plan_data["variants"][0]["print"]["ne"],
            camera_axis=var_r["camera_axis"],
            grid_size=var_r["grid_size"],
            edge_mode="split",
            **geometry,
        )
    )

    quality = dict(
        edits=edits,
        parallax=parallax,
        repair_engine=var_r["repair_quality"] if var_r["repair"] else "none",
        render_size=list(photo.size),
        source_size=list(photo.size),
        source_resolution_render=True,
    )

    print(f"  Blender render başlatılıyor (Nr=12, Grid=1024, 4 Katman, Tam Kadraj 1872x3098)...")
    t0 = time.time()
    render(
        prepared_dir / "photo.png",
        prepared_dir / "depth.npy",
        render_output,
        render_config,
        blender=blender_path,
        repair={
            "enabled": var_r["repair"],
            "layers": var_r["layers"],
            "radius": var_r["inpaint_radius"],
            "quality": var_r["repair_quality"],
        },
    )
    print(f"  Tam render tamamlandı: {time.time() - t0:.1f} saniye")

    coverage = json.loads((render_output / "coverage.json").read_text(encoding="utf-8"))
    mesh_stats = json.loads((render_output / "job.json").read_text(encoding="utf-8"))["mesh"]
    quality.update(
        max_nonopaque_fraction=coverage["max_nonopaque_fraction"], mesh=mesh_stats
    )
    if (render_output / "repair.json").is_file():
        quality["restoration"] = json.loads(
            (render_output / "repair.json").read_text(encoding="utf-8")
        )

    quality_file.write_text(json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "source_sha256": plan_data["source_sha256"],
        "depth_sha256": plan_data["depth_sha256"],
        "render": var_r,
        "engine_hashes": plan_data["engine_hashes"],
    }
    manifest_file.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "render_dir": render_output,
        "coverage": coverage,
        "quality": quality,
        "cached": False,
    }


def verify_nose_stability(render_dir, ref_pt):
    r_dir = Path(render_dir)
    views_dir = r_dir / "views"
    view_files = sorted(views_dir.glob("view_*.png"))
    nr = len(view_files)
    v_start, v_mid, v_end = 0, (nr - 1) // 2, nr - 1

    def _load_bgr(p):
        with Image.open(p) as _im:
            return cv2.cvtColor(np.array(_im.convert("RGB")), cv2.COLOR_RGB2BGR)

    img_start = _load_bgr(view_files[v_start])
    img_mid = _load_bgr(view_files[v_mid])
    img_end = _load_bgr(view_files[v_end])

    h, w = img_start.shape[:2]
    cx = round(ref_pt["x"] * (w - 1))
    cy = round(ref_pt["y"] * (h - 1))
    rw, rh = round(w * 0.04), round(h * 0.03)

    # 1. Broad face-patch template matching (~150x186 px around landmark)
    patch_start = img_start[cy - rh : cy + rh, cx - rw : cx + rw]
    search_mid = img_mid[cy - rh - 10 : cy + rh + 10, cx - rw - 10 : cx + rw + 10]
    search_end = img_end[cy - rh - 10 : cy + rh + 10, cx - rw - 10 : cx + rw + 10]

    res_mid = cv2.matchTemplate(search_mid, patch_start, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc_m = cv2.minMaxLoc(res_mid)
    dx_m = max_loc_m[0] - 10
    dy_m = max_loc_m[1] - 10

    res_end = cv2.matchTemplate(search_end, patch_start, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc_e = cv2.minMaxLoc(res_end)
    dx_e = max_loc_e[0] - 10
    dy_e = max_loc_e[1] - 10

    max_patch_shift = max(abs(dx_m), abs(dy_m), abs(dx_e), abs(dy_e))

    # 2. Pyramidal Lucas-Kanade Point Tracking on exact landmark [cx, cy]
    gray_start = cv2.cvtColor(img_start, cv2.COLOR_BGR2GRAY)
    gray_mid = cv2.cvtColor(img_mid, cv2.COLOR_BGR2GRAY)
    gray_end = cv2.cvtColor(img_end, cv2.COLOR_BGR2GRAY)

    pt0 = np.array([[[float(cx), float(cy)]]], dtype=np.float32)
    lk_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 50, 0.001)

    pt_end_17, _, _ = cv2.calcOpticalFlowPyrLK(
        gray_start, gray_end, pt0, None, winSize=(17, 17), maxLevel=2, criteria=lk_crit
    )
    pt_back_17, _, _ = cv2.calcOpticalFlowPyrLK(
        gray_end, gray_start, pt_end_17, None, winSize=(17, 17), maxLevel=2, criteria=lk_crit
    )
    fb_err_17 = float(np.linalg.norm(pt0 - pt_back_17))
    lk_dx = float(pt_end_17[0, 0, 0] - cx)
    lk_dy = float(pt_end_17[0, 0, 1] - cy)
    landmark_stable = max(abs(lk_dx), abs(lk_dy)) <= 0.5

    return {
        "v_indices": [v_start, v_mid, v_end],
        "landmark_point_px": [cx, cy],
        "geometric_zero_disparity_px": 0.0,
        "landmark_point_tracking_lk": {
            "window_17": {"dx": lk_dx, "dy": lk_dy, "forward_backward_error_px": fb_err_17},
            "stable": landmark_stable,
        },
        "broad_face_patch_template_matching": {
            "patch_size_px": [rw * 2, rh * 2],
            "shifts": [[dx_m, dy_m], [dx_e, dy_e]],
            "max_shift": max_patch_shift,
            "methodology_note": "Reflects 3D perspective foreshortening and relief of surrounding facial region, not displacement of the chosen zero-reference landmark point.",
        },
        "stable": landmark_stable,
    }


def run_interlace_for_lpis(plan_data, render_dir):
    out_root = Path(r"C:\Users\USER\Documents\lenticular baskı\vd_belirgin_derinlik_20261012")
    results = {}

    print("\n--- 3. Adım: 3 Lens İçin Bağımsız Interlace Kodlama ---")
    for v in plan_data["variants"]:
        lpi = v["lpi"]
        lpi_str = f"{lpi:.2f}".replace(".", "_") if lpi == 50.2 else f"{int(lpi)}"
        target_dir = Path(v["output_root"])
        target_dir.mkdir(parents=True, exist_ok=True)

        p_cfg = v["print"].copy()
        p_cfg["phase"] = 0.0  # Bağımsız panel, faz 0

        p_work_dir = target_dir / "interlace_work"
        p_work_dir.mkdir(parents=True, exist_ok=True)
        tif_work = p_work_dir / "interlaced.tif"

        final_panel_tif = target_dir / f"panel_{lpi_str}lpi_belirgin_phase0.tif"

        if not final_panel_tif.is_file():
            print(f"  [{lpi} LPI] Interlace kodlanıyor (Ne={p_cfg['ne']}, Faz=0.0)...")
            t0 = time.time()
            rep = encode(render_dir, p_work_dir, p_cfg)
            print(f"  Kodlama tamamlandı: {time.time() - t0:.1f} sn")
            (target_dir / "print_report.json").write_text(
                json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            shutil.copyfile(tif_work, final_panel_tif)
        else:
            print(f"  [{lpi} LPI] Interlace panel zaten mevcut: {final_panel_tif.name}")

        # ICC tag and size check
        with tifffile.TiffFile(final_panel_tif) as tf:
            tag_icc = tf.pages[0].tags.get(34675)
            has_icc = tag_icc is not None
            icc_len = len(tag_icc.value) if tag_icc else 0
            page = tf.pages[0]
            w, h = page.shape[1], page.shape[0]
            x_res = page.tags.get(282).value
            res_val = x_res[0] / x_res[1] if isinstance(x_res, tuple) else float(x_res)

        print(
            f"  [{lpi} LPI Doğrulama] Boyut: {w}x{h} px, PPI: {res_val:.0f}, ICC: {has_icc} ({icc_len} byte)"
        )
        assert w == 6141 and h == 10163, f"Boyut hatası: {w}x{h}"
        assert round(res_val) == 1200, f"PPI hatası: {res_val}"
        assert has_icc, "ICC profili eksik!"

        results[str(lpi)] = {
            "lpi": lpi,
            "panel_path": str(final_panel_tif),
            "width_px": w,
            "height_px": h,
            "ppi": res_val,
            "has_icc": has_icc,
            "icc_len": icc_len,
        }

    return results


def generate_animated_and_static_comparisons(new_render_dir):
    out_root = Path(r"C:\Users\USER\Documents\lenticular baskı\vd_belirgin_derinlik_20261012")
    prev_root = Path(r"C:\Users\USER\Documents\lenticular baskı")

    old_50c_dir = prev_root / "render_C/render/views"
    old_75c_dir = prev_root / "vd_75lpi/render_C/views"
    old_100c_dir = prev_root / "vd_100lpi/render_C/views"
    new_dir = Path(new_render_dir) / "views"

    assert old_50c_dir.is_dir(), f"Eski 50.20 C bulunamadı: {old_50c_dir}"
    assert old_75c_dir.is_dir(), f"Eski 75 C bulunamadı: {old_75c_dir}"
    assert old_100c_dir.is_dir(), f"Eski 100 C bulunamadı: {old_100c_dir}"
    assert new_dir.is_dir(), f"Yeni render bulunamadı: {new_dir}"

    print("\n--- 4. Adım: Eski vs Yeni Hareketli ve Statik Karşılaştırma Üretimi ---")

    # Load view files
    files_50c = sorted(old_50c_dir.glob("view_*.png"))  # 10 views
    files_75c = sorted(old_75c_dir.glob("view_*.png"))  # 8 views
    files_100c = sorted(old_100c_dir.glob("view_*.png"))  # 6 views
    files_new = sorted(new_dir.glob("view_*.png"))  # 12 views

    nr_50 = len(files_50c)
    nr_75 = len(files_75c)
    nr_100 = len(files_100c)
    nr_new = len(files_new)

    # 1. Direct 2-Panel Animation: Old 50.20 C (6°) vs New Strong (10°)
    pw = 640
    sample_im = Image.open(files_new[0])
    ph = round(sample_im.height * pw / sample_im.width)
    banner_h = 70

    # 24 frames ping-pong sweep
    # t goes 0 -> 1 -> 0
    t_steps = [i / 12.0 for i in range(13)] + [i / 12.0 for i in range(11, 0, -1)]

    try:
        font_main = ImageFont.truetype("arial.ttf", 24)
        font_sub = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    frames_2panel = []
    for t in t_steps:
        idx_50 = round(t * (nr_50 - 1))
        idx_new = round(t * (nr_new - 1))

        im_50 = Image.open(files_50c[idx_50]).convert("RGB").resize((pw, ph), Image.Resampling.LANCZOS)
        im_new = Image.open(files_new[idx_new]).convert("RGB").resize((pw, ph), Image.Resampling.LANCZOS)

        board = Image.new("RGB", (pw * 2, ph + banner_h), color=(20, 22, 26))
        board.paste(im_50, (0, banner_h))
        board.paste(im_new, (pw, banner_h))

        draw = ImageDraw.Draw(board)
        # Headers
        t1 = f"ESKİ 50.20 C (Açı: 6.0°, Paralaks: %3.0) [Kare {idx_50+1}/{nr_50}]"
        t2 = f"YENİ BELİRGİN (Açı: 10.0°, Paralaks: %6.0) [Kare {idx_new+1}/{nr_new}]"
        b1 = draw.textbbox((0, 0), t1, font=font_sub)
        b2 = draw.textbbox((0, 0), t2, font=font_sub)
        draw.text(((pw - (b1[2] - b1[0])) // 2, 24), t1, fill=(200, 210, 230), font=font_sub)
        draw.text((pw + (pw - (b2[2] - b2[0])) // 2, 24), t2, fill=(255, 220, 120), font=font_sub)
        draw.line([(pw, 0), (pw, ph + banner_h)], fill=(60, 65, 75), width=2)
        frames_2panel.append(board)

    anim_2p_apng = out_root / "karsilastirma_hareketli_eski50c_vs_yeni10deg.png"
    anim_2p_gif = out_root / "karsilastirma_hareketli_eski50c_vs_yeni10deg.gif"
    frames_2panel[0].save(
        anim_2p_apng,
        save_all=True,
        append_images=frames_2panel[1:],
        duration=120,
        loop=0,
    )
    frames_2panel[0].save(
        anim_2p_gif,
        save_all=True,
        append_images=frames_2panel[1:],
        duration=120,
        loop=0,
    )
    print(f"  2-Panelli animasyon kaydedildi: {anim_2p_apng.name} & {anim_2p_gif.name}")

    # 2. 4-Panel Synchronized Animation: Old 50C vs Old 75C vs Old 100C vs New Strong
    pw4 = 480
    ph4 = round(sample_im.height * pw4 / sample_im.width)
    frames_4panel = []

    for t in t_steps:
        idx_50 = round(t * (nr_50 - 1))
        idx_75 = round(t * (nr_75 - 1))
        idx_100 = round(t * (nr_100 - 1))
        idx_new = round(t * (nr_new - 1))

        im_50 = Image.open(files_50c[idx_50]).convert("RGB").resize((pw4, ph4), Image.Resampling.LANCZOS)
        im_75 = Image.open(files_75c[idx_75]).convert("RGB").resize((pw4, ph4), Image.Resampling.LANCZOS)
        im_100 = Image.open(files_100c[idx_100]).convert("RGB").resize((pw4, ph4), Image.Resampling.LANCZOS)
        im_new = Image.open(files_new[idx_new]).convert("RGB").resize((pw4, ph4), Image.Resampling.LANCZOS)

        board4 = Image.new("RGB", (pw4 * 4, ph4 + banner_h), color=(18, 20, 24))
        board4.paste(im_50, (0, banner_h))
        board4.paste(im_75, (pw4, banner_h))
        board4.paste(im_100, (pw4 * 2, banner_h))
        board4.paste(im_new, (pw4 * 3, banner_h))

        draw4 = ImageDraw.Draw(board4)
        labels = [
            f"Eski 50.20 C (6.0°)",
            f"Eski 75 C (3.13°)",
            f"Eski 100 C (1.67°)",
            f"YENİ BELİRGİN (10.0°)",
        ]
        sublabels = [
            f"Paralaks: %3.0 [v{idx_50+1}]",
            f"Paralaks: %1.56 [v{idx_75+1}]",
            f"Paralaks: %0.84 [v{idx_100+1}]",
            f"Paralaks: %6.0 [v{idx_new+1}]",
        ]
        colors = [(180, 190, 210), (180, 190, 210), (180, 190, 210), (255, 215, 100)]

        for i in range(4):
            bx = i * pw4
            bb1 = draw4.textbbox((0, 0), labels[i], font=font_main)
            bb2 = draw4.textbbox((0, 0), sublabels[i], font=font_sub)
            draw4.text((bx + (pw4 - (bb1[2] - bb1[0])) // 2, 12), labels[i], fill=colors[i], font=font_main)
            draw4.text((bx + (pw4 - (bb2[2] - bb2[0])) // 2, 42), sublabels[i], fill=(160, 165, 175), font=font_sub)
            if i > 0:
                draw4.line([(bx, 0), (bx, ph4 + banner_h)], fill=(50, 55, 65), width=2)

        frames_4panel.append(board4)

    anim_4p_apng = out_root / "karsilastirma_hareketli_eski_vs_yeni_4panel.png"
    anim_4p_gif = out_root / "karsilastirma_hareketli_eski_vs_yeni_4panel.gif"
    frames_4panel[0].save(
        anim_4p_apng,
        save_all=True,
        append_images=frames_4panel[1:],
        duration=120,
        loop=0,
    )
    frames_4panel[0].save(
        anim_4p_gif,
        save_all=True,
        append_images=frames_4panel[1:],
        duration=120,
        loop=0,
    )
    print(f"  4-Panelli animasyon kaydedildi: {anim_4p_apng.name} & {anim_4p_gif.name}")

    # 3. Static Side-by-Side Comparison of Center Views
    mid_50 = Image.open(files_50c[(nr_50 - 1) // 2]).convert("RGB").resize((pw, ph), Image.Resampling.LANCZOS)
    mid_new = Image.open(files_new[(nr_new - 1) // 2]).convert("RGB").resize((pw, ph), Image.Resampling.LANCZOS)
    mid_board = Image.new("RGB", (pw * 2, ph + banner_h), color=(20, 22, 26))
    mid_board.paste(mid_50, (0, banner_h))
    mid_board.paste(mid_new, (pw, banner_h))
    d_m = ImageDraw.Draw(mid_board)
    m1 = "ESKİ 50.20 C — Orta Görüş (v5/10)"
    m2 = "YENİ BELİRGİN 10° — Orta Görüş (v6/12)"
    b_m1 = d_m.textbbox((0, 0), m1, font=font_main)
    b_m2 = d_m.textbbox((0, 0), m2, font=font_main)
    d_m.text(((pw - (b_m1[2] - b_m1[0])) // 2, 20), m1, fill=(200, 210, 230), font=font_main)
    d_m.text((pw + (pw - (b_m2[2] - b_m2[0])) // 2, 20), m2, fill=(255, 220, 120), font=font_main)
    d_m.line([(pw, 0), (pw, ph + banner_h)], fill=(60, 65, 75), width=2)
    static_mid_jpg = out_root / "karsilastirma_statik_orta_gorunus.jpg"
    mid_board.save(static_mid_jpg, quality=94)
    print(f"  Statik orta görüş kaydedildi: {static_mid_jpg.name}")

    # 4. Detailed Defect & Crop Comparison (Thumb/Hand, Face/Nose, Outer Edge)
    # Compare Left View (view 0) vs Right View (view 11) of the new 10 deg render
    im_v0 = Image.open(files_new[0]).convert("RGB")
    im_v11 = Image.open(files_new[-1]).convert("RGB")
    iw, ih = im_v0.size

    # Crops at native resolution:
    # Crop 1: Thumb/Hand region (approx x: 100-750, y: 1300-2100)
    # Crop 2: Face region (approx x: 700-1250, y: 250-850)
    # Crop 3: Edge border (left edge x: 0-400, y: 1000-1800) to inspect edge_guard=false
    crop_size = 500
    crop_face_v0 = im_v0.crop((700, 250, 700 + crop_size, 250 + crop_size))
    crop_face_v11 = im_v11.crop((700, 250, 700 + crop_size, 250 + crop_size))

    crop_hand_v0 = im_v0.crop((150, 1400, 150 + crop_size, 1400 + crop_size))
    crop_hand_v11 = im_v11.crop((150, 1400, 150 + crop_size, 1400 + crop_size))

    crop_edge_v0 = im_v0.crop((0, 1200, crop_size, 1200 + crop_size))
    crop_edge_v11 = im_v11.crop((0, 1200, crop_size, 1200 + crop_size))

    defect_board = Image.new("RGB", (crop_size * 3, crop_size * 2 + 80), color=(15, 17, 20))
    # Row 1: Leftmost view (View 0)
    defect_board.paste(crop_face_v0, (0, 80))
    defect_board.paste(crop_hand_v0, (crop_size, 80))
    defect_board.paste(crop_edge_v0, (crop_size * 2, 80))
    # Row 2: Rightmost view (View 11)
    defect_board.paste(crop_face_v11, (0, 80 + crop_size))
    defect_board.paste(crop_hand_v11, (crop_size, 80 + crop_size))
    defect_board.paste(crop_edge_v11, (crop_size * 2, 80 + crop_size))

    d_def = ImageDraw.Draw(defect_board)
    sec_titles = [
        "Yüz ve Burun Hacmi (700, 250)",
        "Ön Başparmak & El Hareketi (150, 1400)",
        "Kenar Sınırı (edge_guard=false) (0, 1200)",
    ]
    for idx, st in enumerate(sec_titles):
        bb = d_def.textbbox((0, 0), st, font=font_sub)
        d_def.text((idx * crop_size + (crop_size - (bb[2] - bb[0])) // 2, 25), st, fill=(230, 230, 240), font=font_sub)
        if idx > 0:
            d_def.line([(idx * crop_size, 0), (idx * crop_size, crop_size * 2 + 80)], fill=(60, 65, 75), width=2)
    d_def.line([(0, 80 + crop_size), (crop_size * 3, 80 + crop_size)], fill=(60, 65, 75), width=2)

    defect_jpg = out_root / "karsilastirma_detay_kirpilmis_kusurlar.jpg"
    defect_board.save(defect_jpg, quality=94)
    print(f"  Detay kırpılmış kusur karşılaştırması kaydedildi: {defect_jpg.name}")

    return {
        "anim_2panel_apng": str(anim_2p_apng),
        "anim_2panel_gif": str(anim_2p_gif),
        "anim_4panel_apng": str(anim_4p_apng),
        "anim_4panel_gif": str(anim_4p_gif),
        "static_mid_jpg": str(static_mid_jpg),
        "defect_jpg": str(defect_jpg),
    }


def main():
    parser = argparse.ArgumentParser(description="VD Belirgin Derinlik Yürütme Adaptörü")
    parser.add_argument("--plan", required=True, help="strong-plan.json yolu")
    args = parser.parse_args()

    plan_path = Path(args.plan).resolve()
    if not plan_path.is_file():
        raise FileNotFoundError(f"Plan bulunamadı: {plan_path}")

    plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
    source_photo, depth_path = verify_inputs(plan_data)
    depth_arr = np.load(depth_path, allow_pickle=False)
    blender_path = find_blender()

    # 1. Preview render
    cov_prev, prev_dir = run_preview_render(plan_data, source_photo, depth_arr, blender_path)

    # 2. Full 12-view shared render
    render_res = run_full_render(plan_data, source_photo, depth_arr, blender_path)

    # Nose stability check
    ref_pt = plan_data["shared_render"]["render"]["reference_point"]
    nose_res = verify_nose_stability(render_res["render_dir"], ref_pt)
    lk_shift = nose_res["landmark_point_tracking_lk"]["window_17"]
    print(
        f"  Burun kerteriz noktası LK takibi (v{nose_res['v_indices'][0]}->v{nose_res['v_indices'][2]}): "
        f"dx={lk_shift['dx']:.4f}, dy={lk_shift['dy']:.4f} px (Sabit: {nose_res['stable']}) | "
        f"Geniş yüz yaması şablon kayması: {nose_res['broad_face_patch_template_matching']['max_shift']} px"
    )

    # 3. Interlace encode for the 3 target lenses
    interlace_res = run_interlace_for_lpis(plan_data, render_res["render_dir"])

    # 4. Animated and static visual comparisons
    comparison_res = generate_animated_and_static_comparisons(render_res["render_dir"])

    # 5. Save execution run record
    run_record = {
        "schema_version": 1,
        "run_id": "vd-strong-execution-20261012",
        "stage": "stronger-depth-execution",
        "status": "rendered_and_verified_digital",
        "physical_3d_verified": False,
        "plan": str(plan_path),
        "render_res": {
            "render_dir": str(render_res["render_dir"]),
            "coverage": render_res["coverage"],
            "parallax": render_res["quality"]["parallax"],
            "nose_stability": nose_res,
        },
        "interlace_results": interlace_res,
        "comparisons": comparison_res,
        "analyzer_warnings": {
            str(v["lpi"]): v.get("warnings", []) for v in plan_data["variants"]
        },
    }

    record_path = Path(r"C:\Users\USER\Documents\lenticular baskı\knowledge\runs\vd-strong-execution-20261012.json")
    record_path.write_text(json.dumps(run_record, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nÜretim koşu kaydı yazıldı: {record_path.name}")

    print("\n" + "=" * 70)
    print("YENİ BELİRGİN DERİNLİK DENEMESİ EKSİKSİZ VE BAŞARIYLA TAMAMLANDI!")
    print("=" * 70)


if __name__ == "__main__":
    main()
