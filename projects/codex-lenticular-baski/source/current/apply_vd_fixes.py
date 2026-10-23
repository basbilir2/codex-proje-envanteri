"""Script to apply two targeted fixes to VD lenticular trial outputs:
1. Verify ICC profiles in panel TIFFs, embed in the two combined TIFFs, and verify RGB pixel preservation.
2. Generate clean side-by-side static and animated multi-view comparison previews from rendered views (not interlaced raster).
3. Update print note wording in baski-notu.md.
"""
import sys
import io
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageCms
import tifffile

WORK_DIR = Path(r"C:\Users\USER\Documents\lenticular baskı")

def fix_1_embed_icc():
    print("=" * 60)
    print("DÜZELTME 1: ICC Profili Doğrulama ve Birleşik TIFF'lere Gömme")
    print("=" * 60)
    
    panel_files = [
        WORK_DIR / "panel_A_bagimsiz_phase0.tif",
        WORK_DIR / "panel_B_bagimsiz_phase0.tif",
        WORK_DIR / "panel_C_bagimsiz_phase0.tif",
    ]
    
    profiles = []
    for p in panel_files:
        with tifffile.TiffFile(p) as tif:
            tag = tif.pages[0].tags.get(34675)
            assert tag is not None, f"{p.name} dosyasında ICC profil etiketi (34675) bulunamadı!"
            raw_bytes = bytes(tag.value)
            prof_obj = ImageCms.ImageCmsProfile(io.BytesIO(raw_bytes))
            desc = prof_obj.profile.profile_description
            print(f"{p.name}: ICC profili bulundu (uzunluk: {len(raw_bytes)} bayt, tanım: '{desc}')")
            profiles.append(raw_bytes)
            
    # Check that profile lengths and parameters are identical
    p0_obj = ImageCms.ImageCmsProfile(io.BytesIO(profiles[0]))
    for idx, p_bytes in enumerate(profiles[1:], start=1):
        p_obj = ImageCms.ImageCmsProfile(io.BytesIO(p_bytes))
        assert p_obj.profile.profile_description == p0_obj.profile.profile_description
        assert p_obj.profile.xcolor_space == p0_obj.profile.xcolor_space
        assert p_obj.profile.connection_space == p0_obj.profile.connection_space
        assert len(p_bytes) == len(profiles[0])
    print("DOĞRULAMA: Üç panel TIFF'inde de sRGB yerleşik ICC profili eksiksiz ve uyumlu.")
    
    chosen_icc = profiles[0]
    
    combined_files = [
        (WORK_DIR / "karsilastirma_sayfasi_etiketli_1200ppi.tif", (10446, 18423, 3)),
        (WORK_DIR / "karsilastirma_sayfasi_resim_alani_1200ppi.tif", (10163, 18423, 3))
    ]
    
    for tif_path, expected_shape in combined_files:
        print(f"\nİşleniyor: {tif_path.name}")
        # Read existing image data and metadata
        with tifffile.TiffFile(tif_path) as tif:
            page = tif.pages[0]
            orig_shape = page.shape
            orig_dtype = page.dtype
            orig_res = (page.tags[282].value, page.tags[283].value) # XResolution, YResolution
            orig_res_unit = page.tags[296].value # ResolutionUnit
            assert orig_shape == expected_shape, f"Beklenmeyen boyut: {orig_shape} vs {expected_shape}"
            orig_data = tif.asarray()
            
        print(f"  Mevcut boyut: {orig_shape}, Dtype: {orig_dtype}, Çözünürlük: {orig_res[0][0]}/{orig_res[0][1]} DPI")
        
        # Rewrite with identical pixels, dimensions, resolution, and embed ICC profile tag 34675
        temp_path = tif_path.with_suffix(".tmp.tif")
        with tifffile.TiffWriter(temp_path, bigtiff=orig_data.nbytes > 3_500_000_000) as writer:
            writer.write(
                orig_data,
                photometric="rgb",
                resolution=(1200, 1200),
                resolutionunit="INCH",
                rowsperstrip=128,
                extratags=[(34675, "B", len(chosen_icc), chosen_icc, False)]
            )
            
        # Verify rewritten file
        with tifffile.TiffFile(temp_path) as verify_tif:
            v_page = verify_tif.pages[0]
            assert v_page.shape == expected_shape, "Yazılan TIFF boyutu eşleşmiyor!"
            tag = v_page.tags.get(34675)
            assert tag is not None and bytes(tag.value) == chosen_icc, "ICC profili yazılamadı veya eşleşmiyor!"
            v_res_x = v_page.tags[282].value
            v_res_y = v_page.tags[283].value
            v_res_unit = v_page.tags[296].value
            assert v_res_x[0] / v_res_x[1] == 1200 and v_res_y[0] / v_res_y[1] == 1200
            assert v_res_unit == 2 # Inch
            v_data = verify_tif.asarray()
            assert np.array_equal(v_data, orig_data), "RGB piksel değerlerinde sapma tespit edildi!"
            
        # Atomic replace
        temp_path.replace(tif_path)
        print(f"  BAŞARILI: {tif_path.name} içine ICC profili gömüldü. Pikseller, boyut ve 1200 PPI %100 korundu.")


def fix_2_multiview_previews():
    print("\n" + "=" * 60)
    print("DÜZELTME 2: Kamera Karelerinden Eşzamanlı Karşılaştırma ve Hareketli Önizleme")
    print("=" * 60)
    
    views_A = WORK_DIR / "render_A" / "render" / "views"
    views_B = WORK_DIR / "render_B" / "render" / "views"
    views_C = WORK_DIR / "render_C" / "render" / "views"
    
    nr = 10
    for idx in range(nr):
        assert (views_A / f"view_{idx:04d}.png").is_file()
        assert (views_B / f"view_{idx:04d}.png").is_file()
        assert (views_C / f"view_{idx:04d}.png").is_file()
    print("10 adet render kamera karesi A, B ve C klasörlerinde doğrulandı.")
    
    # 1. Clean side-by-side static comparison of the central view (view 4 / 0 deg center)
    center_idx = 4
    imA = Image.open(views_A / f"view_{center_idx:04d}.png").convert("RGB")
    imB = Image.open(views_B / f"view_{center_idx:04d}.png").convert("RGB")
    imC = Image.open(views_C / f"view_{center_idx:04d}.png").convert("RGB")
    
    src_w, src_h = imA.size # 1872, 3098
    target_panel_w = 960
    target_panel_h = round(src_h * target_panel_w / src_w) # 1587
    
    resA = imA.resize((target_panel_w, target_panel_h), Image.Resampling.LANCZOS)
    resB = imB.resize((target_panel_w, target_panel_h), Image.Resampling.LANCZOS)
    resC = imC.resize((target_panel_w, target_panel_h), Image.Resampling.LANCZOS)
    
    total_w = target_panel_w * 3
    header_h = 90
    board = Image.new("RGB", (total_w, target_panel_h + header_h), color=(25, 27, 32))
    board.paste(resA, (0, header_h))
    board.paste(resB, (target_panel_w, header_h))
    board.paste(resC, (target_panel_w * 2, header_h))
    
    draw = ImageDraw.Draw(board)
    try:
        font = ImageFont.truetype("arial.ttf", 32)
        subfont = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
        subfont = ImageFont.load_default()
        
    labels = [
        ("A - Normal (3.0° Açı / %1.0 Ön / %1.5 Arka)", 0),
        ("B - Artırılmış (4.5° Açı / %1.5 Ön / %2.2 Arka)", target_panel_w),
        ("C - Güçlü (6.0° Açı / %2.0 Ön / %3.0 Arka)", target_panel_w * 2)
    ]
    
    for title, x_off in labels:
        bb = draw.textbbox((0, 0), title, font=font)
        tw = bb[2] - bb[0]
        draw.text((x_off + (target_panel_w - tw) // 2, 28), title, fill=(240, 240, 245), font=font)
        if x_off > 0:
            draw.line([(x_off, 0), (x_off, target_panel_h + header_h)], fill=(60, 65, 75), width=2)
            
    static_preview_path = WORK_DIR / "karsilastirma_temiz_gorunusler_merkez.jpg"
    board.save(static_preview_path, quality=92)
    print(f"Statik merkez görüş karşılaştırması kaydedildi: {static_preview_path.name} ({total_w}x{target_panel_h + header_h} px)")
    
    # 2. Animated simultaneous 3-variant comparison preview across all 10 views
    print("Eşzamanlı 3-varyant hareketli önizleme kareleri hazırlanıyor...")
    anim_panel_w = 640
    anim_panel_h = round(src_h * anim_panel_w / src_w) # 1058
    anim_tot_w = anim_panel_w * 3 # 1920
    anim_header_h = 70
    
    try:
        a_font = ImageFont.truetype("arial.ttf", 24)
        a_tagfont = ImageFont.truetype("arial.ttf", 18)
    except OSError:
        a_font = ImageFont.load_default()
        a_tagfont = ImageFont.load_default()
        
    frames = []
    for idx in range(nr):
        fA = Image.open(views_A / f"view_{idx:04d}.png").convert("RGB").resize((anim_panel_w, anim_panel_h), Image.Resampling.LANCZOS)
        fB = Image.open(views_B / f"view_{idx:04d}.png").convert("RGB").resize((anim_panel_w, anim_panel_h), Image.Resampling.LANCZOS)
        fC = Image.open(views_C / f"view_{idx:04d}.png").convert("RGB").resize((anim_panel_w, anim_panel_h), Image.Resampling.LANCZOS)
        
        frame_canvas = Image.new("RGB", (anim_tot_w, anim_panel_h + anim_header_h), color=(20, 22, 26))
        frame_canvas.paste(fA, (0, anim_header_h))
        frame_canvas.paste(fB, (anim_panel_w, anim_header_h))
        frame_canvas.paste(fC, (anim_panel_w * 2, anim_header_h))
        
        fdraw = ImageDraw.Draw(frame_canvas)
        v_label = f"Kamera Görüşü {idx + 1} / {nr}"
        
        titles = [
            f"A - Normal (3.0°) — {v_label}",
            f"B - Artırılmış (4.5°) — {v_label}",
            f"C - Güçlü (6.0°) — {v_label}"
        ]
        for c_idx, title in enumerate(titles):
            x_off = c_idx * anim_panel_w
            bb = fdraw.textbbox((0, 0), title, font=a_font)
            tw = bb[2] - bb[0]
            fdraw.text((x_off + (anim_panel_w - tw) // 2, 22), title, fill=(235, 235, 240), font=a_font)
            if c_idx > 0:
                fdraw.line([(x_off, 0), (x_off, anim_panel_h + anim_header_h)], fill=(50, 55, 65), width=2)
                
        frames.append(frame_canvas)
        
    # Forward and backward sequence for smooth continuous look-around
    ping_pong = frames + frames[-2:0:-1]
    
    # Save as APNG (highest quality 24-bit RGB)
    anim_apng_path = WORK_DIR / "karsilastirma_hareketli_look_around.png"
    ping_pong[0].save(
        anim_apng_path,
        save_all=True,
        append_images=ping_pong[1:],
        duration=180,
        loop=0
    )
    print(f"Hareketli APNG önizlemesi kaydedildi: {anim_apng_path.name}")
    
    # Save interactive HTML viewer with slider for exact inspection
    html_viewer_dir = WORK_DIR / "multiview_comparison_html"
    html_viewer_dir.mkdir(parents=True, exist_ok=True)
    frame_filenames = []
    for idx, f in enumerate(frames):
        fname = f"frame_{idx:02d}.jpg"
        f.save(html_viewer_dir / fname, quality=88)
        frame_filenames.append(fname)
        
    html_content = f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<title>VD Üç Derinlik Eşzamanlı Görüş Karşılaştırması</title>
<style>
body {{ font-family: system-ui, sans-serif; background: #181a1f; color: #eee; margin: 0; padding: 20px; display: flex; flex-direction: column; align-items: center; }}
h1 {{ font-size: 20px; margin-bottom: 8px; color: #fff; }}
p {{ margin: 0 0 16px 0; color: #aaa; font-size: 14px; }}
.viewport {{ max-width: 100%; border: 1px solid #333; border-radius: 6px; overflow: hidden; background: #000; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }}
img {{ display: block; max-width: 100%; height: auto; }}
.controls {{ margin-top: 16px; display: flex; align-items: center; gap: 12px; width: 100%; max-width: 900px; }}
button {{ background: #2f68b4; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; font-weight: bold; cursor: pointer; }}
button:hover {{ background: #3b7ed8; }}
input[type=range] {{ flex: 1; accent-color: #3b7ed8; cursor: pointer; }}
.label {{ font-size: 15px; font-weight: bold; min-width: 90px; text-align: right; }}
</style>
</head>
<body>
<h1>VD — Normal / Artırılmış / Güçlü Eşzamanlı Kamera Görünüşleri</h1>
<p>Kamera kareleri doğrudan 3D Blender sahnesinden alınmıştır (interlaced baskı TIFF'i değildir). Üç varyantın paralaks ve derinlik farkı aynı açı adımlarıyla yan yana izlenebilir.</p>
<div class="viewport">
  <img id="viewImg" src="{frame_filenames[4]}" alt="Görünüş Karşılaştırması">
</div>
<div class="controls">
  <button id="playBtn">Durdur</button>
  <input type="range" id="slider" min="0" max="{nr - 1}" value="4" step="1">
  <span class="label" id="posLabel">Görüş 5 / {nr}</span>
</div>
<script>
const frames = {json.dumps(frame_filenames)};
const img = document.getElementById('viewImg');
const slider = document.getElementById('slider');
const label = document.getElementById('posLabel');
const btn = document.getElementById('playBtn');
let idx = 4, dir = 1, timer = null;

frames.forEach(src => {{ const pre = new Image(); pre.src = src; }});

function show(n) {{
  idx = n;
  slider.value = n;
  img.src = frames[n];
  label.textContent = `Görüş ${{n + 1}} / ${{frames.length}}`;
}}

slider.oninput = () => {{
  stop();
  show(Number(slider.value));
}};

function tick() {{
  if (idx === frames.length - 1) dir = -1;
  if (idx === 0) dir = 1;
  show(idx + dir);
}}

function play() {{
  btn.textContent = 'Durdur';
  timer = setInterval(tick, 180);
}}

function stop() {{
  clearInterval(timer);
  timer = null;
  btn.textContent = 'Oynat';
}}

btn.onclick = () => {{
  if (timer) stop(); else play();
}};

play();
</script>
</body>
</html>
"""
    html_path = WORK_DIR / "karsilastirma_hareketli_onizleme.html"
    html_path.write_text(html_content, encoding="utf-8")
    print(f"İnteraktif web oynatıcısı kaydedildi: {html_path.name}")


def fix_3_update_baski_notu():
    print("\n" + "=" * 60)
    print("DÜZELTME 3: baski-notu.md İfade Düzeltmesi")
    print("=" * 60)
    
    note_path = WORK_DIR / "baski-notu.md"
    content = note_path.read_text(encoding="utf-8")
    
    target_phrase = "- **Kanal Başına Raster Piksel:** 2.3904 piksel (Kanal ayrımı matematiksel olarak yeterlidir)"
    new_phrase = "- **Kanal Başına Raster Piksel:** Kanal başına 2,3904 raster piksel hesaplanmıştır; fiziksel kanal ayrımı henüz doğrulanmamıştır."
    
    assert target_phrase in content, "Hedef ifade baski-notu.md içinde bulunamadı!"
    updated = content.replace(target_phrase, new_phrase)
    note_path.write_text(updated, encoding="utf-8")
    print("baski-notu.md başarıyla güncellendi:")
    print(f"  Yeni ifade: '{new_phrase}'")

def main():
    fix_1_embed_icc()
    fix_2_multiview_previews()
    fix_3_update_baski_notu()
    print("\n" + "=" * 60)
    print("TÜM İSTENEN DÜZELTMELER VE DOĞRULAMALAR BAŞARIYLA TAMAMLANDI!")
    print("=" * 60)

if __name__ == "__main__":
    main()
