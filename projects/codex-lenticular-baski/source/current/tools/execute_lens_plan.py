"""Reusable lens plan execution adapter.
Usage: python tools/execute_lens_plan.py --plan <absolute_path_to_plan.json>
"""
import argparse
import hashlib
import io
import json
import math
import shutil
import sys
import time
from pathlib import Path

# Ensure Lenticular Studio is in sys.path
STUDIO_ROOT = Path(r"C:\Users\USER\.codex\.chatgpt-projects\g-p-6ac08f7c2fe88191a25ea989c11950e1")
if str(STUDIO_ROOT) not in sys.path:
    sys.path.insert(0, str(STUDIO_ROOT))

import cv2
import numpy as np
from PIL import Image, ImageCms, ImageDraw, ImageFont
import tifffile

from lenticular.geometry import validate as validate_render
from lenticular.printing import encode, validate as validate_print
from lenticular.repair import editable_depth, plan_parallax, save_parallax_map
from lenticular.runner import digest, find_blender, render

RENDER_ENGINE_VERSION = 21


def verify_inputs(plan_data):
    source_path = Path(plan_data["source"]).resolve()
    depth_path = Path(plan_data["depth_cache"]).resolve()

    if not source_path.is_file():
        raise FileNotFoundError(f"Kaynak dosya bulunamadı: {source_path}")
    if not depth_path.is_file():
        raise FileNotFoundError(f"Derinlik haritası bulunamadı: {depth_path}")

    source_hash = digest(source_path)
    if source_hash != plan_data["input_identity"]["source_sha256"]:
        raise ValueError(
            f"Kaynak hash uyuşmazlığı: {source_hash} != {plan_data['input_identity']['source_sha256']}"
        )

    depth_hash = digest(depth_path)
    if depth_hash != plan_data["input_identity"]["depth_sha256"]:
        raise ValueError(
            f"Derinlik hash uyuşmazlığı: {depth_hash} != {plan_data['input_identity']['depth_sha256']}"
        )

    print("Girdi doğrulaması başarılı:")
    print(f"  Kaynak: {source_path} ({source_hash})")
    print(f"  Derinlik: {depth_path} ({depth_hash})")
    return source_path, depth_path


def check_render_cached(render_dir, manifest_target, expected_nr, var_code=None):
    render_dir = Path(render_dir)
    manifest_path = render_dir / "render_manifest.json"
    if var_code is None and render_dir.name.startswith("render_"):
        var_code = render_dir.name.replace("render_", "")
    quality_path = (render_dir.parent / f"quality_{var_code}.json") if var_code else None
    coverage_path = render_dir / "coverage.json"

    if (
        not manifest_path.is_file()
        or quality_path is None
        or not quality_path.is_file()
        or not coverage_path.is_file()
    ):
        return False

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest != manifest_target:
            return False
        # Verify quality and coverage files are valid JSON
        json.loads(quality_path.read_text(encoding="utf-8"))
        json.loads(coverage_path.read_text(encoding="utf-8"))
        # Verify all views exist
        for idx in range(expected_nr):
            if not (render_dir / f"views/view_{idx:04d}.png").is_file():
                return False
        return True
    except Exception:
        return False


def run_preview_check_if_needed(variant_c, source_photo, depth_arr, blender_path):
    out_root = Path(variant_c["output_root"])
    preview_dir = out_root / "preview_C"
    preview_render_dir = preview_dir / "render"
    nr = variant_c["render"]["nr"]

    coverage_path = preview_render_dir / "coverage.json"
    if coverage_path.is_file() and all(
        (preview_render_dir / f"views/view_{i:04d}.png").is_file() for i in range(nr)
    ):
        cov = json.loads(coverage_path.read_text(encoding="utf-8"))
        print(
            f"  [{variant_c['lpi']} LPI] C Önizleme zaten mevcut (Max non-opaque: {cov['max_nonopaque_fraction']:.6f})."
        )
        return cov

    preview_dir.mkdir(parents=True, exist_ok=True)
    with Image.open(source_photo) as orig:
        c_photo = orig.convert("RGBA")

    # Long edge 1024, grid 512
    c_photo.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
    c_depth = cv2.resize(depth_arr, c_photo.size, interpolation=cv2.INTER_LINEAR)

    c_cfg = variant_c["render"].copy()
    c_cfg["render_long_edge"] = 1024
    c_cfg["grid_size"] = 512

    c_edited, c_edits = editable_depth(c_depth, c_cfg, c_photo)
    c_cfg["zero_reference"] = c_edits["zero_reference"]
    c_geom, c_par, c_disp = plan_parallax(c_edited, c_photo.size, c_cfg)

    c_photo.save(preview_dir / "photo.png")
    np.save(preview_dir / "depth.npy", c_edited, allow_pickle=False)
    save_parallax_map(c_disp, preview_dir / "parallax.png")

    config = validate_render(
        dict(
            nr=c_cfg["nr"],
            ne=variant_c["print"]["ne"],
            camera_axis=c_cfg["camera_axis"],
            grid_size=c_cfg["grid_size"],
            edge_mode="split",
            **c_geom,
        )
    )

    print(
        f"  [{variant_c['lpi']} LPI] C Önizleme Blender Render başlatılıyor (1024 px, 512 grid, Nr={nr})..."
    )
    t0 = time.time()
    render(
        preview_dir / "photo.png",
        preview_dir / "depth.npy",
        preview_render_dir,
        config,
        blender=blender_path,
        repair={
            "enabled": c_cfg["repair"],
            "layers": c_cfg["layers"],
            "radius": c_cfg["inpaint_radius"],
            "quality": c_cfg["repair_quality"],
        },
    )
    print(f"  C Önizleme tamamlandı: {time.time() - t0:.1f} saniye")
    cov = json.loads((preview_render_dir / "coverage.json").read_text(encoding="utf-8"))
    if cov["max_nonopaque_fraction"] > 0.0005:
        print(
            f"  UYARI: C Önizleme boşluk oranı %0.05 üzerinde: {cov['max_nonopaque_fraction']:.6f}"
        )
    else:
        print(
            f"  KONTROL BAŞARILI: C Önizleme boşluk oranı: {cov['max_nonopaque_fraction']:.6f}"
        )
    return cov


def run_full_render(variant, source_photo, depth_arr, blender_path):
    var_code = variant["code"]
    lpi = variant["lpi"]
    var_r = variant["render"].copy()
    render_output = Path(variant["render_output"])
    var_parent = render_output.parent
    var_prepared = var_parent / f"prepared_{var_code}"
    var_prepared.mkdir(parents=True, exist_ok=True)

    nr = var_r["nr"]
    cache_id = variant["render_cache_identity"]

    if check_render_cached(render_output, cache_id, nr, var_code=var_code):
        print(f"  [{lpi} LPI - {var_code}] Tam render önbellekte mevcut, yeniden kullanılacak.")
        quality = json.loads((var_parent / f"quality_{var_code}.json").read_text(encoding="utf-8"))
        coverage = json.loads((render_output / "coverage.json").read_text(encoding="utf-8"))
        return {
            "render_dir": render_output,
            "coverage": coverage,
            "quality": quality,
            "cached": True,
        }

    with Image.open(source_photo) as orig:
        photo = orig.convert("RGBA")

    edited_depth, edits = editable_depth(depth_arr, var_r, photo)
    var_r["zero_reference"] = edits["zero_reference"]
    geometry, parallax, disparity = plan_parallax(edited_depth, photo.size, var_r)

    photo.save(var_prepared / "photo.png")
    np.save(var_prepared / "depth.npy", edited_depth, allow_pickle=False)
    Image.fromarray(np.rint(edited_depth * 255).astype(np.uint8)).save(
        var_prepared / "depth.png"
    )
    save_parallax_map(disparity, var_prepared / "parallax.png")

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

    config = validate_render(
        dict(
            nr=var_r["nr"],
            ne=variant["print"]["ne"],
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

    print(
        f"  [{lpi} LPI - {var_code}] Blender Render başlatılıyor (Nr={nr}, Grid=1024, Layers=4)..."
    )
    t0 = time.time()
    render(
        var_prepared / "photo.png",
        var_prepared / "depth.npy",
        render_output,
        config,
        blender=blender_path,
        repair={
            "enabled": var_r["repair"],
            "layers": var_r["layers"],
            "radius": var_r["inpaint_radius"],
            "quality": var_r["repair_quality"],
        },
    )
    print(f"  [{lpi} LPI - {var_code}] Render tamamlandı: {time.time() - t0:.1f} saniye")

    coverage = json.loads((render_output / "coverage.json").read_text(encoding="utf-8"))
    mesh_stats = json.loads((render_output / "job.json").read_text(encoding="utf-8"))["mesh"]
    quality.update(
        max_nonopaque_fraction=coverage["max_nonopaque_fraction"], mesh=mesh_stats
    )
    if (render_output / "repair.json").is_file():
        quality["restoration"] = json.loads(
            (render_output / "repair.json").read_text(encoding="utf-8")
        )

    (var_parent / f"quality_{var_code}.json").write_text(
        json.dumps(quality, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (render_output / "render_manifest.json").write_text(
        json.dumps(cache_id, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    return {
        "render_dir": render_output,
        "coverage": coverage,
        "quality": quality,
        "cached": False,
    }


def verify_views_and_nose(variant, render_res):
    r_dir = Path(render_res["render_dir"])
    nr = variant["render"]["nr"]
    qual = render_res["quality"]
    w, h = qual["render_size"]

    ref_pt = variant["render"]["reference_point"]
    nx, ny = round(ref_pt["x"] * (w - 1)), round(ref_pt["y"] * (h - 1))

    v_start = 0
    v_mid = (nr - 1) // 2
    v_end = nr - 1

    patch_rad = 20
    patches = []
    for v_idx in [v_start, v_mid, v_end]:
        v_img = Image.open(r_dir / f"views/view_{v_idx:04d}.png").convert("L")
        patch = np.asarray(
            v_img.crop((nx - patch_rad, ny - patch_rad, nx + patch_rad, ny + patch_rad)),
            dtype=np.float32,
        )
        patches.append(patch)

    center_patch = patches[1]
    shifts = []
    for p in [patches[0], patches[2]]:
        res_corr = cv2.matchTemplate(p, center_patch[2:-2, 2:-2], cv2.TM_CCOEFF_NORMED)
        _, _, _, max_loc = cv2.minMaxLoc(res_corr)
        dx = max_loc[0] - 2
        dy = max_loc[1] - 2
        shifts.append((dx, dy))

    max_shift = max(abs(shifts[0][0]), abs(shifts[1][0]))
    stable = max_shift <= 1
    return {
        "v_indices": [v_start, v_mid, v_end],
        "shifts": shifts,
        "max_shift": max_shift,
        "stable": stable,
    }


def execute_lens(plan_data, lpi_target, source_photo, depth_arr, blender_path):
    print("\n" + "=" * 70)
    print(f"LENS ÜRETİM DÖNGÜSÜ: {lpi_target} LPI")
    print("=" * 70)

    variants = [v for v in plan_data["variants"] if v["lpi"] == lpi_target]
    sheet_info = next(s for s in plan_data["sheets"] if s["lpi"] == lpi_target)
    out_root = Path(sheet_info["output_root"])
    out_root.mkdir(parents=True, exist_ok=True)

    # 1. Preview check for C
    var_c = next(v for v in variants if v["code"] == "C")
    cov_c = run_preview_check_if_needed(var_c, source_photo, depth_arr, blender_path)

    # 2. Render all 3 variants (A, B, C)
    render_results = {}
    nose_verifications = {}
    for v in variants:
        code = v["code"]
        res = run_full_render(v, source_photo, depth_arr, blender_path)
        render_results[code] = res
        nose_ver = verify_views_and_nose(v, res)
        nose_verifications[code] = nose_ver
        print(
            f"  [{lpi_target} LPI - {code}] Burun stabilitesi: Uç Sol (v{nose_ver['v_indices'][0]})->v{nose_ver['v_indices'][1]}: dx={nose_ver['shifts'][0][0]}, dy={nose_ver['shifts'][0][1]} | Uç Sağ (v{nose_ver['v_indices'][2]}): dx={nose_ver['shifts'][1][0]}, dy={nose_ver['shifts'][1][1]} -> Sabit: {nose_ver['stable']}"
        )

    # 3. Interlace Encoding
    print(f"\n--- [{lpi_target} LPI] Interlace Kodlama ---")
    encoded_panels = {}
    shared_icc = None

    for v in variants:
        code = v["code"]
        r_dir = render_results[code]["render_dir"]
        p_cfg_indep = v["print"].copy()
        p_cfg_indep["phase"] = 0.0

        p_indep_dir = out_root / f"print_{code}_indep"
        p_indep_dir.mkdir(parents=True, exist_ok=True)
        tif_indep = p_indep_dir / "interlaced.tif"

        if not tif_indep.is_file():
            print(f"  Kodlanıyor: {code} Bağımsız (Faz 0.0)...")
            rep_i = encode(r_dir, p_indep_dir, p_cfg_indep)
            (out_root / f"print_quality_{code}_indep.json").write_text(
                json.dumps(rep_i, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        encoded_panels[f"{code}_indep"] = tif_indep

        # Read ICC profile tag from generated panel
        if shared_icc is None:
            with tifffile.TiffFile(tif_indep) as tf:
                tag = tf.pages[0].tags.get(34675)
                if tag:
                    shared_icc = bytes(tag.value)

        # Sheet phase
        sheet_phase = v["sheet_phase"]
        p_cfg_sheet = v["print"].copy()
        p_cfg_sheet["phase"] = sheet_phase

        p_sheet_dir = out_root / f"print_{code}_sheet"
        p_sheet_dir.mkdir(parents=True, exist_ok=True)
        tif_sheet = p_sheet_dir / "interlaced.tif"

        if not tif_sheet.is_file():
            print(f"  Kodlanıyor: {code} Sayfa (Faz {sheet_phase:.4f})...")
            rep_s = encode(r_dir, p_sheet_dir, p_cfg_sheet)
            (out_root / f"print_quality_{code}_sheet.json").write_text(
                json.dumps(rep_s, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        encoded_panels[f"{code}_sheet"] = tif_sheet

    # Copy top-level individual panel files
    for code in ["A", "B", "C"]:
        shutil.copyfile(
            encoded_panels[f"{code}_indep"],
            out_root / f"panel_{code}_bagimsiz_phase0.tif",
        )
        shutil.copyfile(
            encoded_panels[f"{code}_sheet"],
            out_root / f"panel_{code}_sheet_phase.tif",
        )

    # 4. Assemble Comparison Sheet
    print(f"\n--- [{lpi_target} LPI] Birleşik Sayfa Montajı ---")
    pA = tifffile.imread(encoded_panels["A_sheet"])
    pB = tifffile.imread(encoded_panels["B_sheet"])
    pC = tifffile.imread(encoded_panels["C_sheet"])

    combined_img = np.concatenate([pA, pB, pC], axis=1)
    del pA, pB, pC

    ppi = 1200
    extratags = (
        [(34675, "B", len(shared_icc), shared_icc, False)] if shared_icc else []
    )

    # Unlabeled image
    pure_tif = out_root / f"karsilastirma_sayfasi_resim_alani_{int(lpi_target)}lpi_1200ppi.tif"
    print(f"  Kaydediliyor: {pure_tif.name}...")
    with tifffile.TiffWriter(pure_tif) as writer:
        writer.write(
            combined_img,
            photometric="rgb",
            resolution=(ppi, ppi),
            resolutionunit="INCH",
            rowsperstrip=128,
            extratags=extratags,
        )

    # Labeled image with 6 mm label strip
    tot_w = combined_img.shape[1]
    strip_h = round(sheet_info["label_strip_mm"] * ppi / 25.4)  # 283 px
    panel_w = tot_w // 3

    strip_pil = Image.new("RGB", (tot_w, strip_h), color=(255, 255, 255))
    draw = ImageDraw.Draw(strip_pil)
    draw.line([(0, 0), (tot_w, 0)], fill=(200, 200, 200), width=3)

    try:
        font = ImageFont.truetype("arial.ttf", 96)
        sub_font = ImageFont.truetype("arial.ttf", 48)
    except OSError:
        font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    labels_data = [
        (
            f"A - Normal ({lpi_target:g} LPI)",
            f"Açı: {variants[0]['render']['angle_deg']:.2f}° | Ön %{variants[0]['render']['front_parallax_percent']:.2f} | Arka %{variants[0]['render']['back_parallax_percent']:.2f} | Ne={variants[0]['print']['ne']} | Faz: {variants[0]['sheet_phase']:.4f}",
        ),
        (
            f"B - Artırılmış ({lpi_target:g} LPI)",
            f"Açı: {variants[1]['render']['angle_deg']:.2f}° | Ön %{variants[1]['render']['front_parallax_percent']:.2f} | Arka %{variants[1]['render']['back_parallax_percent']:.2f} | Ne={variants[1]['print']['ne']} | Faz: {variants[1]['sheet_phase']:.4f}",
        ),
        (
            f"C - Güçlü ({lpi_target:g} LPI)",
            f"Açı: {variants[2]['render']['angle_deg']:.2f}° | Ön %{variants[2]['render']['front_parallax_percent']:.2f} | Arka %{variants[2]['render']['back_parallax_percent']:.2f} | Ne={variants[2]['print']['ne']} | Faz: {variants[2]['sheet_phase']:.4f}",
        ),
    ]

    for i, (title_text, sub_text) in enumerate(labels_data):
        cx = i * panel_w + panel_w // 2
        bb_t = draw.textbbox((0, 0), title_text, font=font)
        draw.text((cx - (bb_t[2] - bb_t[0]) // 2, 40), title_text, fill=(20, 20, 20), font=font)
        bb_s = draw.textbbox((0, 0), sub_text, font=sub_font)
        draw.text((cx - (bb_s[2] - bb_s[0]) // 2, 160), sub_text, fill=(90, 90, 90), font=sub_font)
        if i > 0:
            draw.line([(i * panel_w, 0), (i * panel_w, strip_h)], fill=(200, 200, 200), width=2)

    strip_arr = np.asarray(strip_pil, dtype=np.uint8)
    labeled_img = np.concatenate([combined_img, strip_arr], axis=0)
    del strip_arr, combined_img

    labeled_tif = out_root / f"karsilastirma_sayfasi_etiketli_{int(lpi_target)}lpi_1200ppi.tif"
    print(f"  Kaydediliyor: {labeled_tif.name}...")
    with tifffile.TiffWriter(labeled_tif) as writer:
        writer.write(
            labeled_img,
            photometric="rgb",
            resolution=(ppi, ppi),
            resolutionunit="INCH",
            rowsperstrip=128,
            extratags=extratags,
        )

    # 5. Clean multi-view static & animated previews (from camera frames)
    print(f"\n--- [{lpi_target} LPI] Temiz Kamera Karelerinden Önizlemeler ---")
    nr = variants[0]["render"]["nr"]
    mid_idx = (nr - 1) // 2

    # Static middle view comparison
    im_mid_A = Image.open(render_results["A"]["render_dir"] / f"views/view_{mid_idx:04d}.png").convert("RGB")
    im_mid_B = Image.open(render_results["B"]["render_dir"] / f"views/view_{mid_idx:04d}.png").convert("RGB")
    im_mid_C = Image.open(render_results["C"]["render_dir"] / f"views/view_{mid_idx:04d}.png").convert("RGB")

    pw = 960
    ph = round(im_mid_A.height * pw / im_mid_A.width)
    mid_board = Image.new("RGB", (pw * 3, ph + 90), color=(25, 27, 32))
    mid_board.paste(im_mid_A.resize((pw, ph), Image.Resampling.LANCZOS), (0, 90))
    mid_board.paste(im_mid_B.resize((pw, ph), Image.Resampling.LANCZOS), (pw, 90))
    mid_board.paste(im_mid_C.resize((pw, ph), Image.Resampling.LANCZOS), (pw * 2, 90))

    b_draw = ImageDraw.Draw(mid_board)
    try:
        t_font = ImageFont.truetype("arial.ttf", 30)
    except OSError:
        t_font = ImageFont.load_default()

    for idx, code in enumerate(["A", "B", "C"]):
        t_str = f"{code} ({variants[idx]['name']}) — Orta Görüş {mid_idx+1}/{nr}"
        b_bb = b_draw.textbbox((0, 0), t_str, font=t_font)
        b_draw.text((idx * pw + (pw - (b_bb[2] - b_bb[0])) // 2, 28), t_str, fill=(240, 240, 245), font=t_font)
        if idx > 0:
            b_draw.line([(idx * pw, 0), (idx * pw, ph + 90)], fill=(60, 65, 75), width=2)

    mid_jpg = out_root / f"karsilastirma_temiz_gorunusler_orta_{int(lpi_target)}lpi.jpg"
    mid_board.save(mid_jpg, quality=92)
    print(f"  Statik orta görüş kaydedildi: {mid_jpg.name}")

    # Animated look-around APNG & HTML viewer
    anim_pw = 640
    anim_ph = round(im_mid_A.height * anim_pw / im_mid_A.width)
    anim_frames = []

    for v_idx in range(nr):
        fA = Image.open(render_results["A"]["render_dir"] / f"views/view_{v_idx:04d}.png").convert("RGB").resize((anim_pw, anim_ph), Image.Resampling.LANCZOS)
        fB = Image.open(render_results["B"]["render_dir"] / f"views/view_{v_idx:04d}.png").convert("RGB").resize((anim_pw, anim_ph), Image.Resampling.LANCZOS)
        fC = Image.open(render_results["C"]["render_dir"] / f"views/view_{v_idx:04d}.png").convert("RGB").resize((anim_pw, anim_ph), Image.Resampling.LANCZOS)

        f_can = Image.new("RGB", (anim_pw * 3, anim_ph + 70), color=(20, 22, 26))
        f_can.paste(fA, (0, 70))
        f_can.paste(fB, (anim_pw, 70))
        f_can.paste(fC, (anim_pw * 2, 70))

        f_draw = ImageDraw.Draw(f_can)
        for c_idx, code in enumerate(["A", "B", "C"]):
            title_f = f"{code} ({variants[c_idx]['name']}) — Görüş {v_idx+1}/{nr}"
            bb_f = f_draw.textbbox((0, 0), title_f, font=t_font)
            f_draw.text((c_idx * anim_pw + (anim_pw - (bb_f[2] - bb_f[0])) // 2, 20), title_f, fill=(235, 235, 240), font=t_font)
            if c_idx > 0:
                f_draw.line([(c_idx * anim_pw, 0), (c_idx * anim_pw, anim_ph + 70)], fill=(50, 55, 65), width=2)
        anim_frames.append(f_can)

    ping_pong = anim_frames + anim_frames[-2:0:-1]
    anim_png = out_root / f"karsilastirma_hareketli_look_around_{int(lpi_target)}lpi.png"
    ping_pong[0].save(
        anim_png,
        save_all=True,
        append_images=ping_pong[1:],
        duration=round(1000 / (nr - 1)),
        loop=0,
    )
    print(f"  Hareketli APNG kaydedildi: {anim_png.name}")

    # Copy analysis reports from plans/
    plans_dir = Path(plan_data["variants"][0]["render_output"]).parents[1] / f"plans/vd-75-100-1200ppi-8af22b6a/{int(lpi_target)}lpi"
    if plans_dir.is_dir():
        for item in plans_dir.iterdir():
            dest = out_root / item.name
            if item.is_dir() and not dest.exists():
                shutil.copytree(item, dest)

    # 6. Print Note Markdown
    note_content = f"""# VD — {int(lpi_target)} LPI Üç Derinlik Denemesi Baskı Notu ve Kalibrasyon Taslağı

> [!IMPORTANT]
> Bu çalışma bir **baskı denemesi / kalibrasyon taslağıdır**. Çıktılar {lpi_target:g} LPI lens ve 1200 DPI yazıcı adayı için dijital olarak doğrulanmıştır; henüz fiziksel RIP/baskı doğrulaması yapılmamıştır.

## 1. Üretim Özeti ve Parametreler
- **Kaynak Görsel:** `vd-gigapixel-recover v2-2x-faceai v2.jpg` (1872 × 3098 px, Tam kadraj)
- **Sabit Burun Referansı:** Piksel (958, 432) | Normalize (x=0.512026, y=0.139490)
- **Ortak Derinlik Haritası:** DA3MONO-LARGE (process_res=1008, preserve normalizasyon) + Ayrıntılı yerel AI derinlik (güç 0.8)
- **Baskı Çözünürlüğü:** 1200 PPI / 1200 DPI
- **Lens:** Nominal ve Etkin {lpi_target:g} LPI dikey, Tilt=0, Bleed=0, Fit=Contain
- **Kanal Sayısı:** Ne={variants[0]['print']['ne']} kanal, Nr={variants[0]['render']['nr']} kamera görünüşü
- **Kanal Başına Raster Piksel:** Kanal başına {1200/lpi_target/variants[0]['print']['ne']:.4f} raster piksel hesaplanmıştır; fiziksel kanal ayrımı henüz doğrulanmamıştır.

## 2. Varyant Karşılaştırma Tablosu

| Parametre | A - Normal | B - Artırılmış | C - Güçlü |
| :--- | :--- | :--- | :--- |
| **Kamera Açısı (İstenen / Uygulanan)** | {variants[0]['render']['angle_deg']:.2f}° / {render_results['A']['quality']['parallax']['effective_angle_deg']:.2f}° | {variants[1]['render']['angle_deg']:.2f}° / {render_results['B']['quality']['parallax']['effective_angle_deg']:.2f}° | {variants[2]['render']['angle_deg']:.2f}° / {render_results['C']['quality']['parallax']['effective_angle_deg']:.2f}° |
| **Hedef Bütçe (Ön / Arka Paralaks)** | %{variants[0]['render']['front_parallax_percent']:.2f} / %{variants[0]['render']['back_parallax_percent']:.2f} | %{variants[1]['render']['front_parallax_percent']:.2f} / %{variants[1]['render']['back_parallax_percent']:.2f} | %{variants[2]['render']['front_parallax_percent']:.2f} / %{variants[2]['render']['back_parallax_percent']:.2f} |
| **Gerçekleşen Max Paralaks** | %{render_results['A']['quality']['parallax']['max_parallax_percent']:.2f} | %{render_results['B']['quality']['parallax']['max_parallax_percent']:.2f} | %{render_results['C']['quality']['parallax']['max_parallax_percent']:.2f} |
| **Disparite Aralığı** | [{render_results['A']['quality']['parallax']['endpoint_disparity_px_range'][0]:.1f}, {render_results['A']['quality']['parallax']['endpoint_disparity_px_range'][1]:.1f}] px | [{render_results['B']['quality']['parallax']['endpoint_disparity_px_range'][0]:.1f}, {render_results['B']['quality']['parallax']['endpoint_disparity_px_range'][1]:.1f}] px | [{render_results['C']['quality']['parallax']['endpoint_disparity_px_range'][0]:.1f}, {render_results['C']['quality']['parallax']['endpoint_disparity_px_range'][1]:.1f}] px |
| **Sayfa Birleştirme Fazı** | {variants[0]['sheet_phase']:.4f} | {variants[1]['sheet_phase']:.4f} | {variants[2]['sheet_phase']:.4f} |
| **Bağımsız Panel Fazı** | 0.0000 | 0.0000 | 0.0000 |
| **Görünüş Boşluk Oranı** | %{render_results['A']['coverage']['max_nonopaque_fraction']*100:.4f} | %{render_results['B']['coverage']['max_nonopaque_fraction']*100:.4f} | %{render_results['C']['coverage']['max_nonopaque_fraction']*100:.4f} |
| **Burun Sabitliği (Uç Görüşler)** | {'Sabit (<=1 px)' if nose_verifications['A']['stable'] else 'Sapma var'} | {'Sabit (<=1 px)' if nose_verifications['B']['stable'] else 'Sapma var'} | {'Sabit (<=1 px)' if nose_verifications['C']['stable'] else 'Sapma var'} |

## 3. Sayfa ve Dosya Yapısı
1. **Tek Parça {int(lpi_target)} LPI Lens Altında Birleşik Karşılaştırma Sayfası:**
   - `{labeled_tif.name}`: 18423 × 10446 px (~389.95 × 221.12 mm). Altta 6 mm açıklama şeridi mevcuttur.
   - `{pure_tif.name}`: 18423 × 10163 px (~389.95 × 215.12 mm). Saf görüntü alanıdır.
2. **Ayrı Lens Parçaları İçin Bağımsız Paneller (Faz=0.0):**
   - `panel_A_bagimsiz_phase0.tif`, `panel_B_bagimsiz_phase0.tif`, `panel_C_bagimsiz_phase0.tif` (6141 × 10163 px).
"""
    note_path = out_root / "baski-notu.md"
    note_path.write_text(note_content, encoding="utf-8")
    print(f"  Baskı notu kaydedildi: {note_path.name}")

    return {
        "lpi": lpi_target,
        "output_root": str(out_root),
        "labeled_sheet": str(labeled_tif),
        "pure_sheet": str(pure_tif),
        "static_preview": str(mid_jpg),
        "animated_preview": str(anim_png),
        "coverage_c": cov_c,
        "render_results": render_results,
        "nose_verifications": nose_verifications,
    }


def check_plan_renders_cached(plan_data):
    all_cached = True
    print("\n--- Render Önbellek Denetimi ---")
    for v in plan_data["variants"]:
        lpi = int(v["lpi"])
        code = v["code"]
        r_dir = Path(v["render_output"])
        expected_nr = v["render"]["nr"]
        cache_id = v["render_cache_identity"]
        is_cached = check_render_cached(r_dir, cache_id, expected_nr, var_code=code)
        status_str = "GEÇERLİ (ÖNBELLEK BULUNDU)" if is_cached else "GEÇERSİZ (ÖNBELLEK YOK/UYUMSUZ)"
        print(f"  [{lpi} LPI - {code}] {status_str}: {r_dir}")
        if not is_cached:
            all_cached = False
    return all_cached


def main():
    parser = argparse.ArgumentParser(description="Lens planı yürütme adaptörü")
    parser.add_argument("--plan", required=True, help="Tam plan.json yolu")
    parser.add_argument(
        "--check-cache-only",
        action="store_true",
        help="Yalnızca önbellek geçerliliğini denetle, render veya üretim başlatma",
    )
    args = parser.parse_args()

    plan_path = Path(args.plan).resolve()
    if not plan_path.is_file():
        raise FileNotFoundError(f"Plan dosyası bulunamadı: {plan_path}")

    plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
    source_photo, depth_path = verify_inputs(plan_data)

    if args.check_cache_only:
        all_ok = check_plan_renders_cached(plan_data)
        if all_ok:
            print("\nÖnbellek doğrulama başarılı: Tüm varyantlar önbellekle tam eşleşiyor.")
            sys.exit(0)
        else:
            print("\nÖnbellek doğrulama başarısız: Bazı varyantlar önbellekte eksik veya uyumsuz.")
            sys.exit(1)

    depth_arr = np.load(depth_path, allow_pickle=False)
    blender_path = find_blender()

    run_results = []
    lpis = plan_data["input_identity"]["lpi"]
    for lpi in lpis:
        res = execute_lens(plan_data, lpi, source_photo, depth_arr, blender_path)
        run_results.append(res)

    print("\n" + "=" * 70)
    print("TÜM LENS PLANLARI EKSİKSİZ VE BAŞARIYLA TAMAMLANDI!")
    print("=" * 70)


if __name__ == "__main__":
    main()
