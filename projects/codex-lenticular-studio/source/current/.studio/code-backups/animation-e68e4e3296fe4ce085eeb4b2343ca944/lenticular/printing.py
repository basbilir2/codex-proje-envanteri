"""Lenticular raster encoding, lens simulation and physical calibration artifacts."""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageDraw, ImageFont
import tifffile

from .runner import digest


DEFAULTS = dict(width_mm=100.0, height_mm=100.0, bleed_mm=0.0, ppi=600.0,
    printer_dpi=1200.0, nominal_lpi=60.0, effective_lpi=60.0, ne=10,
    axis="vertical", phase=0.0, tilt_deg=0.0, reverse_views=False, mirror=False,
    fit="cover", stripe_sampling="center", crosstalk=0.0, compensation=0.0,
    regularization=0.02, crosstalk_matrix=None, icc_path=None, color_mode="RGB",
    white_underbase=False, pitch_verified=False, viewing_distance_mm=500.0,
    lens_view_angle_deg=30.0, allow_unfilled=False,pitch_step=.01,pitch_candidates=11,
    gamut_guard=True)


def validate(settings, require_color_profile=True):
    if not isinstance(settings, dict) or set(settings)-set(DEFAULTS):
        raise ValueError("Baskı ayarları geçersiz veya bilinmeyen alan içeriyor.")
    result = DEFAULTS | settings
    ranges = dict(width_mm=(5, 3000), height_mm=(5, 3000), bleed_mm=(0, 50),
        ppi=(30, 4800), printer_dpi=(30, 9600), nominal_lpi=(1, 300),
        effective_lpi=(1, 300), phase=(-1000, 1000), tilt_deg=(-10, 10),
        crosstalk=(0, .45), compensation=(0, 1), regularization=(.001, 1),
        viewing_distance_mm=(50, 20000), lens_view_angle_deg=(1, 90),pitch_step=(.0001,1))
    for key, (low, high) in ranges.items():
        value = result[key]
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"Baskı ayarı {key}: {low}–{high} arasında olmalı.")
    if type(result["ne"]) is not int or not 2 <= result["ne"] <= 64:
        raise ValueError("Baskı kanalı Ne 2–64 arasında olmalı.")
    if type(result["pitch_candidates"]) is not int or not 3 <= result["pitch_candidates"] <= 31 or result["pitch_candidates"]%2 == 0:
        raise ValueError("Pitch adayı sayısı 3–31 arasında tek sayı olmalı.")
    if result["effective_lpi"]-result["pitch_step"]*(result["pitch_candidates"]-1)/2 <= 0:
        raise ValueError("Pitch test aralığı pozitif LPI değerleri içermeli.")
    for key, choices in dict(axis=("vertical", "horizontal"), fit=("cover", "contain"),
        stripe_sampling=("center", "area"), color_mode=("RGB", "CMYK")).items():
        if result[key] not in choices:
            raise ValueError(f"Geçersiz {key} ayarı.")
    for key in ("reverse_views", "mirror", "white_underbase", "pitch_verified", "allow_unfilled", "gamut_guard"):
        if type(result[key]) is not bool:
            raise ValueError(f"{key} doğru/yanlış olmalı.")
    if require_color_profile and result["color_mode"] == "CMYK" and not result["icc_path"]:
        raise ValueError("CMYK çıktı için yazıcı/mürekkep/malzeme ICC profili seçin.")
    width = round((result["width_mm"]+2*result["bleed_mm"])*result["ppi"]/25.4)
    height = round((result["height_mm"]+2*result["bleed_mm"])*result["ppi"]/25.4)
    if width*height > 500_000_000 or max(width, height) > 100000:
        raise ValueError("Çıktı 500 megapikseli veya bir kenarda 100000 pikseli aşamaz; boyut/PPI azaltın.")
    return result


def mixing_matrix(settings):
    count = settings["ne"]
    supplied = settings["crosstalk_matrix"]
    if supplied is not None:
        matrix = np.asarray(supplied, dtype=np.float64)
        if matrix.shape != (count, count) or not np.isfinite(matrix).all() or np.any(matrix < 0) or np.any(matrix.sum(1) <= 0):
            raise ValueError("Ölçülmüş karışım matrisi Ne×Ne boyutunda ve negatif olmayan değerler içermeli.")
        matrix = matrix / matrix.sum(1, keepdims=True)
    else:
        matrix = np.eye(count, dtype=np.float64)
        amount = settings["crosstalk"]
        for i in range(count):
            neighbors = [j for j in (i-1, i+1) if 0 <= j < count]
            matrix[i, i] = 1-amount
            for j in neighbors:
                matrix[i, j] = amount/len(neighbors)
    if settings["compensation"] and np.linalg.cond(matrix) > 1e4:
        raise ValueError("Karışım matrisi telafi için kararsız; ölçümü veya telafi ayarını düzeltin.")
    return matrix


def compensation_matrix(settings, mixing):
    strength = settings["compensation"]
    if not strength:
        return np.eye(settings["ne"], dtype=np.float32)
    reg = settings["regularization"]
    # Tikhonov prior around identity preserves constant colors, unlike zero-prior damping.
    identity = np.eye(settings["ne"])
    inverse = np.linalg.solve(mixing.T@mixing + reg*identity, mixing.T + reg*identity)
    return ((1-strength)*identity + strength*inverse).astype(np.float32)


def to_linear(values):
    values = np.asarray(values, dtype=np.float32)/255
    return np.where(values <= .04045, values/12.92, ((values+.055)/1.055)**2.4)


def from_linear(values):
    values = np.clip(values, 0, 1)
    return np.clip(np.rint(255*np.where(values <= .0031308, 12.92*values,
        1.055*np.maximum(values, 0)**(1/2.4)-.055)), 0, 255).astype(np.uint8)


def compensated_frames(frames, inverse, guard):
    original = to_linear(frames)
    adjusted = np.einsum("ij,jhwc->ihwc",inverse,original,optimize=True)
    limited = 0
    if guard:
        delta = adjusted-original
        allowance = np.ones_like(delta)
        np.divide(1-original,delta,out=allowance,where=delta>1e-7)
        np.divide(-original,delta,out=allowance,where=delta < -1e-7)
        # One scale shared by all views and RGB at this point preserves the correction direction.
        scale = np.clip(np.min(allowance,axis=(0,3)),0,1)
        limited = int(np.count_nonzero(scale<.99999))
        adjusted = original+delta*scale[None,:,:,None]
    clipped = int(np.count_nonzero((adjusted < -1e-5)|(adjusted > 1+1e-5)))
    return adjusted,limited,clipped


def frame_mapping(job, settings):
    positions = np.asarray(job["config"]["positions"])
    angles = np.arctan(positions/job["config"]["zero"])
    target = np.linspace(angles[0], angles[-1], settings["ne"])
    indices = np.abs(angles[:, None]-target[None, :]).argmin(0).tolist()
    if settings["reverse_views"]:
        indices.reverse()
    return indices


def load_views(folder, indices, allow_unfilled):
    images, missing = {}, 0.0
    for index in set(indices):
        with Image.open(Path(folder)/f"views/view_{index:04d}.png") as image:
            rgba = np.asarray(image.convert("RGBA"))
        missing = max(missing, float(np.mean(rgba[:, :, 3] < 250)))
        alpha = rgba[:, :, 3:4].astype(np.float32)/255
        images[index] = np.rint(rgba[:, :, :3]*alpha+255*(1-alpha)).astype(np.uint8)
    if missing > .0005 and not allow_unfilled:
        raise ValueError(f"Görünüşlerde %{missing*100:.2f} boş alan var. Arka plan doldurmayı açıp yeniden render alın veya taslak boş alan iznini seçin.")
    return images, missing


def fitted_tile(image, width, height, start, rows, settings, columns=None):
    import cv2
    source_h, source_w = image.shape[:2]
    ppi = settings["ppi"]
    bleed = settings["bleed_mm"]*ppi/25.4
    content_w, content_h = settings["width_mm"]*ppi/25.4, settings["height_mm"]*ppi/25.4
    scale = (max if settings["fit"] == "cover" else min)(content_w/source_w, content_h/source_h)
    x = (np.arange(width, dtype=np.float32) if columns is None else np.asarray(columns,dtype=np.float32))+.5
    if settings["mirror"]:
        x = width-x
    y = np.arange(start, start+rows, dtype=np.float32)+.5
    xs = (x-bleed-(content_w-scale*source_w)/2)/scale-.5
    ys = (y-bleed-(content_h-scale*source_h)/2)/scale-.5
    mx = np.broadcast_to(xs[None, :], (rows, len(xs))).copy()
    my = np.broadcast_to(ys[:, None], (rows, len(xs))).copy()
    tile = cv2.remap(image, mx, my, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    if settings["fit"] == "contain":
        outside = (mx < -.5) | (my < -.5) | (mx >= source_w-.5) | (my >= source_h-.5)
        tile[outside] = 255
    return tile


def channel_pattern(width, start, rows, settings, subpixel=.5):
    bleed = settings["bleed_mm"]*settings["ppi"]/25.4
    sx,sy = (subpixel,subpixel) if np.isscalar(subpixel) else subpixel
    x = np.arange(width, dtype=np.float64)[None, :]+sx-bleed
    if settings["mirror"]:
        x = width-(x+bleed)-bleed
    y = np.arange(start, start+rows, dtype=np.float64)[:, None]+sy-bleed
    tilt = math.radians(settings["tilt_deg"])
    coordinate = (x*math.cos(tilt)+y*math.sin(tilt)) if settings["axis"] == "vertical" else (y*math.cos(tilt)+x*math.sin(tilt))
    phase = (coordinate*settings["effective_lpi"]/settings["ppi"]+settings["phase"]) % 1
    return np.minimum((phase*settings["ne"]).astype(np.int32), settings["ne"]-1)


def color_transform(settings):
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
    destination = ImageCms.getOpenProfile(settings["icc_path"]) if settings["icc_path"] else srgb
    transform = ImageCms.buildTransformFromOpenProfiles(srgb, destination, "RGB", settings["color_mode"], renderingIntent=1)
    return transform, destination.tobytes()


def encode(render_folder, output, settings, progress=None):
    settings = validate(settings)
    render_folder, output = Path(render_folder), Path(output).resolve()
    if "sources" in (p.lower() for p in output.parts) or (output.exists() and any(output.iterdir())):
        raise ValueError("Baskı için sources dışında yeni ve boş klasör kullanın.")
    job = json.loads((render_folder/"job.json").read_text(encoding="utf-8"))
    expected_axis = "x" if settings["axis"] == "vertical" else "y"
    if job["config"].get("camera_axis","x") != expected_axis:
        raise ValueError("Lens çizgileriyle kamera yönü uyuşmuyor. Dikey lens için sağ/sol, yatay lens için yukarı/aşağı kamera render'ı alın.")
    indices = frame_mapping(job, settings)
    images, missing = load_views(render_folder, indices, settings["allow_unfilled"])
    mixing = mixing_matrix(settings)
    inverse = compensation_matrix(settings, mixing)
    transform, profile = color_transform(settings)
    width = round((settings["width_mm"]+2*settings["bleed_mm"])*settings["ppi"]/25.4)
    height = round((settings["height_mm"]+2*settings["bleed_mm"])*settings["ppi"]/25.4)
    channels = 4 if settings["color_mode"] == "CMYK" else 3
    strip_rows = max(1, min(128, int(64*1024**2/(settings["ne"]*width*3*16))))
    clipped, total, limited = 0, 0, 0
    coverage = np.zeros(settings["ne"], dtype=np.float64)
    output.mkdir(parents=True, exist_ok=True)
    sparse = settings['stripe_sampling']=='center' and settings['axis']=='vertical' and settings['tilt_deg']==0 and not settings['compensation']
    if sparse:
        strip_rows=128
        column_pattern=channel_pattern(width,0,1,settings)[0]
        column_groups=[np.flatnonzero(column_pattern==channel) for channel in range(settings['ne'])]

    def strips():
        nonlocal clipped, total, limited
        for start in range(0, height, strip_rows):
            rows = min(strip_rows, height-start)
            if sparse:
                # Sample only each view's printed columns; identical cubic mapping,
                # without allocating Ne copies of a full-width 2400-PPI strip.
                result=np.empty((rows,width,3),dtype=np.uint8)
                for channel,columns in enumerate(column_groups):
                    if columns.size:
                        result[:,columns]=fitted_tile(images[indices[channel]],width,height,start,rows,settings,columns)
                        coverage[channel]+=rows*columns.size
                yield np.asarray(ImageCms.applyTransform(Image.fromarray(result),transform))
                if progress:
                    progress(f"Baskı hazırlanıyor: %{round(100*(start+rows)/height)}")
                continue
            frames = np.stack([fitted_tile(images[i], width, height, start, rows, settings) for i in indices])
            if settings["compensation"]:
                linear,limited_pixels,clipped_values = compensated_frames(frames,inverse,settings["gamut_guard"])
                limited += limited_pixels
                clipped += clipped_values
                total += linear.size
                frames = from_linear(linear)
            if settings["stripe_sampling"] == "center":
                samples = [.5]
            elif settings["tilt_deg"] == 0:
                samples = [((i+.5)/8,.5) if settings["axis"] == "vertical" else (.5,(i+.5)/8) for i in range(8)]
            else:
                samples = [((x+.5)/4,(y+.5)/4) for y in range(4) for x in range(4)]
            # Fractional stripe coverage mixes emitted light, not gamma encoded byte values.
            sampled_frames = to_linear(frames) if len(samples)>1 else frames
            result = np.zeros((rows, width, 3), dtype=np.float32)
            for sample in samples:
                pattern = np.broadcast_to(channel_pattern(width, start, rows, settings, sample), (rows, width))
                coverage[:] += np.bincount(pattern.ravel(),minlength=settings["ne"])/len(samples)
                result += np.take_along_axis(sampled_frames, pattern[None, :, :, None], axis=0)[0]/len(samples)
            tile = Image.fromarray(from_linear(result) if len(samples)>1 else np.rint(result).astype(np.uint8))
            yield np.asarray(ImageCms.applyTransform(tile, transform))
            if progress:
                progress(f"Baskı hazırlanıyor: %{round(100*(start+rows)/height)}")

    target = output/"interlaced.tif"
    with tifffile.TiffWriter(target, bigtiff=width*height*channels > 3_500_000_000) as writer:
        writer.write(data=strips(), shape=(height, width, channels), dtype=np.uint8,
            photometric="separated" if channels == 4 else "rgb", rowsperstrip=strip_rows,
            resolution=(settings["ppi"], settings["ppi"]), resolutionunit="INCH",
            extratags=[(34675, "B", len(profile), profile, False)], metadata=None)
    if settings["white_underbase"]:
        with tifffile.TiffWriter(output/"white-underbase.tif") as writer:
            writer.write(data=(np.full((min(strip_rows, height-y), width), 255, dtype=np.uint8) for y in range(0, height, strip_rows)),
                shape=(height, width), dtype=np.uint8, photometric="minisblack", rowsperstrip=strip_rows,
                resolution=(settings["ppi"], settings["ppi"]), resolutionunit="INCH", metadata=None)
    pitch_test(output, settings, include_response=False)
    registration(output, settings)
    simulation_error = proof(render_folder, output, settings, indices, mixing, inverse)
    warnings = []
    if not settings["pitch_verified"]:
        warnings.append("Etkin LPI gerçek lens/yazıcı pitch baskısı ile doğrulanmadı; çıktı kalibrasyon taslağıdır.")
    if settings["ppi"]/settings["effective_lpi"] < settings["ne"]:
        warnings.append("Lens başına raster piksel sayısı Ne'den az; tüm kanallar ayrı piksellerde temsil edilemeyebilir.")
    if len(set(indices)) < settings["ne"]:
        warnings.append("Nr/Ne seçiminde bazı baskı kanalları aynı render görünüşünü kullanıyor.")
    if settings["compensation"] and settings["crosstalk_matrix"] is None:
        warnings.append("Ghosting telafisi varsayımsal komşu karışımını kullanıyor; fiziksel lens ölçümü değildir.")
    if missing:
        warnings.append("Kaynak görünüşlerdeki şeffaf alanlar beyazla birleştirildi.")
    if np.any(coverage == 0):
        warnings.append("Bazı view kanalları bu PPI/LPI/faz birleşiminde raster piksel alamıyor; Ne veya örnekleme ayarını değiştirin.")
    if clipped/max(total,1) > .05:
        warnings.append("Ghosting telafisinde %5'ten fazla renk değeri kırpılıyor; telafi gücünü azaltmayı değerlendirin.")
    if limited/(width*height) > .05:
        warnings.append(f"Renkleri korumak için görüntünün %{100*limited/(width*height):.1f} bölümünde ghosting telafisi azaltıldı.")
    if simulation_error["after_mse"]>simulation_error["before_mse"]*1.01+1e-8:
        warnings.append("Seçilen telafi lens modelindeki farkı artırıyor; gücü azaltın veya ölçüm matrisini düzeltin.")
    channel_balance = coverage/max(float(coverage.mean()),1)
    if channel_balance.min()<.8 or channel_balance.max()>1.2:
        warnings.append("Baskı kanalları eşit raster payı almıyor; PPI/LPI, Ne ve faz birleşimini kontrol edin.")
    source_w, source_h = next(iter(images.values())).shape[1], next(iter(images.values())).shape[0]
    mm_per_source_pixel = (max if settings["fit"] == "cover" else min)(settings["width_mm"]/source_w,settings["height_mm"]/source_h)
    native_ppi = 25.4/mm_per_source_pixel
    if native_ppi < settings["ppi"]:
        warnings.append(f"Kaynak ayrıntısı yaklaşık {native_ppi:.0f} PPI; {settings['ppi']:.0f} PPI raster çıktı ayrıntıyı yeniden örnekler.")
    depth_estimate = None
    depth_path = render_folder/"depth_proximity.npy"
    if depth_path.is_file():
        d = np.load(depth_path,allow_pickle=False)
        config = job["config"]
        delta = job["mesh"]["focal_px"]*(config["positions"][-1]-config["positions"][0])*(1/config["zero"]-((1-d)/config["far"]+d/config["near"]))
        baseline = 2*settings["viewing_distance_mm"]*math.tan(math.radians(settings["lens_view_angle_deg"])/2)
        slope = delta*mm_per_source_pixel/baseline
        if settings["reverse_views"]:
            slope = -slope
        if np.max(slope) < .95:
            offset = settings["viewing_distance_mm"]*slope/(1-slope)
            depth_estimate = {"plane_offset_mm_range":[float(offset.min()),float(offset.max())],
                "convention":"negative in front of print, positive behind",
                "basis":"ideal endpoint rays and stated lens angle/distance; not a measured optical reconstruction"}
    report = dict(schema_version=1, stage="lenticular_print_preparation", settings=settings,
        nr=job["config"]["nr"], ne=settings["ne"], source_indices=indices,
        raster_size=[width, height], physical_size_mm=[width*25.4/settings["ppi"], height*25.4/settings["ppi"]],
        sampling="nearest rendered angular view; periodic channel raster pattern",
        pixels_per_lens=settings["ppi"]/settings["effective_lpi"], mixing_matrix=mixing.tolist(),
        raster_channel_coverage_fraction=(coverage/(width*height)).tolist(),source_native_ppi=native_ppi,
        ideal_print_depth_estimate=depth_estimate,
        compensation_clipped_fraction=clipped/max(total, 1), nonopaque_source_fraction=missing,
        compensation_limited_fraction=limited/(width*height),simulation_error=simulation_error,
        status="pitch_confirmed_by_user" if settings["pitch_verified"] else "calibration_draft",
        warnings=warnings, source_job_sha256=digest(render_folder/"job.json"),
        interlaced_sha256=digest(target), color_profile_sha256=__import__('hashlib').sha256(profile).hexdigest(),
        white_ink_instructions="Import white-underbase.tif as White in your RIP; it is a separate grayscale mask, not an embedded spot ink.",
        printing_instructions=["Print at 100% physical size without fit-to-page or subsequent resampling.",
            "Use the same RIP, material, lens batch, viewing distance and color settings as the pitch test.",
            "Assign the separate white mask and registration marks in the UV RIP when required.",
            "Animated proof is a simulation and does not verify physical ghosting."])
    (output/"print-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    notes = ["LENTICULAR BASKI TESLİM NOTLARI",f"Görünüş: Nr={report['nr']} · Baskı kanalı: Ne={report['ne']}",
        f"Ölçü: {width*25.4/settings['ppi']:.3f} × {height*25.4/settings['ppi']:.3f} mm · {settings['ppi']:g} PPI",
        f"Etkin lens: {settings['effective_lpi']:g} LPI · Faz: {settings['phase']:g} · Eğim: {settings['tilt_deg']:g}°",
        f"Aynalı çıktı: {'Evet' if settings['mirror'] else 'Hayır'} · Lens çizgileri: {settings['axis']}",
        "", "Dosyayı %100 gerçek ölçekte basın; sayfaya sığdırmayın, yeniden örneklemeyin.",
        "ICC dönüşümü dosyaya uygulanmıştır; RIP'te ikinci kez farklı renk dönüşümü uygulamayın.",
        "Pitch testinde kullanılan lens partisi, malzeme, RIP ve baskı yönünü koruyun.",
        "Beyaz alt baskı dosyası varsa RIP'teki White kanalına atayın.",
        "Kalibrasyon onayı operatör beyanıdır; fiziksel baskı kalite kontrolünü tamamlayın.","", "DEĞERLENDİRME",*warnings]
    (output/"baski-notlari.txt").write_text('\n'.join(notes),encoding="utf-8-sig")
    return report


def pitch_test(output, settings, step=None, candidates=None, include_response=True):
    step = settings.get("pitch_step",.01) if step is None else step
    candidates = settings.get("pitch_candidates",11) if candidates is None else candidates
    ppi = settings["ppi"]
    width = round(settings["width_mm"]*ppi/25.4)
    label_width = round(22*ppi/25.4)
    row_h, header_h = round(10*ppi/25.4), round(13*ppi/25.4)
    height = candidates*row_h+header_h
    if (width+label_width)*height > 150_000_000:
        # Keep full PPI and full printed width; split candidates into labeled pages.
        transform, profile = color_transform(settings)
        try:
            font = ImageFont.truetype("arial.ttf", max(12, round(2.5*ppi/25.4)))
        except OSError:
            font = ImageFont.load_default(size=max(12, round(2.5*ppi/25.4)))
        values=settings["effective_lpi"]+(np.arange(candidates)-(candidates-1)/2)*step
        with tifffile.TiffWriter(Path(output)/'pitch-test.tif') as writer:
            for lpi in values:
                page=Image.new('RGB',(width+label_width,header_h+row_h),'white')
                draw=ImageDraw.Draw(page)
                draw.text((5,5),'PITCH | 100% | NO RESCALE',fill='black',font=font)
                draw.text((3,header_h),f'{lpi:.3f} LPI',fill='black',font=font)
                pattern=(np.floor((np.arange(width)+.5)*lpi/ppi*2).astype(int)%2*255).astype(np.uint8)
                page.paste(Image.fromarray(np.broadcast_to(pattern,(max(1,row_h-round(ppi/25.4)),width)).copy()).convert('RGB'),(label_width,header_h))
                if settings['axis']=='horizontal':page=page.transpose(Image.Transpose.TRANSPOSE)
                if settings['mirror']:page=page.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                pixels=np.asarray(ImageCms.applyTransform(page,transform))
                writer.write(pixels,photometric='separated' if settings['color_mode']=='CMYK' else 'rgb',
                    compression='deflate',resolution=(ppi,ppi),resolutionunit='INCH',metadata=None,
                    extratags=[(34675,'B',len(profile),profile,False)])
        (Path(output)/'pitch-test.json').write_text(json.dumps(dict(candidate_lpi=values.tolist(),ppi=ppi,pages=True,
            instruction='Her sayfa bir LPI adayıdır. %100 ölçekte basın; sayfaları yeniden ölçeklemeyin.'),ensure_ascii=False,indent=2),encoding='utf-8')
        write_matrix_template(output,settings)
        if include_response:crosstalk_chart(output,settings,transform,profile,font)
        return
    image = Image.new("RGB", (width+label_width, height), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", max(12, round(2.5*ppi/25.4)))
    except OSError:
        font = ImageFont.load_default(size=max(12, round(2.5*ppi/25.4)))
    draw.text((5, 5), "PITCH TEST | 100% | NO RESCALE", fill="black", font=font)
    values = settings["effective_lpi"] + (np.arange(candidates)-(candidates-1)/2)*step
    for index, lpi in enumerate(values):
        y = header_h+index*row_h
        pattern = (np.floor((np.arange(width)+.5)*lpi/ppi*2).astype(int)%2*255).astype(np.uint8)
        band = Image.fromarray(np.broadcast_to(pattern, (max(1,row_h-round(ppi/25.4)), width)).copy()).convert("RGB")
        image.paste(band, (label_width, y))
        draw.text((3, y), f"{lpi:.3f} LPI", fill="black", font=font)
    if settings["axis"] == "horizontal":
        image = image.transpose(Image.Transpose.TRANSPOSE)
    if settings["mirror"]:
        image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    transform, profile = color_transform(settings)
    colored = ImageCms.applyTransform(image,transform)
    colored.save(Path(output)/"pitch-test.tif",dpi=(ppi,ppi),compression="tiff_lzw",icc_profile=profile)
    write_matrix_template(output,settings)
    if include_response:crosstalk_chart(output,settings,transform,profile,font)
    (Path(output)/"pitch-test.json").write_text(json.dumps({"candidate_lpi":values.tolist(), "ppi":ppi,
        "instruction":"Aynı lens, yazıcı/RIP, malzeme ve bakış mesafesiyle %100 ölçekte basın. En uniform bandın LPI değerini etkin LPI alanına girin; gerekirse daha dar adımlı testi tekrarlayın."}, ensure_ascii=False, indent=2), encoding="utf-8")


def registration(output, settings):
    ppi = settings["ppi"]
    w = round((settings["width_mm"]+2*settings["bleed_mm"])*ppi/25.4)*25.4/ppi
    h = round((settings["height_mm"]+2*settings["bleed_mm"])*ppi/25.4)*25.4/ppi
    paths = []
    for x, y in ((3,3),(w-3,3),(3,h-3),(w-3,h-3)):
        paths.append(f'<path d="M{x-2},{y}h4 M{x},{y-2}v4"/>')
    pitch = 25.4/settings["effective_lpi"]
    tilt,bleed,phase = math.radians(settings["tilt_deg"]),settings["bleed_mm"],settings["phase"]%1
    normal_length = w+h*abs(math.sin(tilt)) if settings["axis"] == "vertical" else h+w*abs(math.sin(tilt))
    for k in range(-math.ceil(normal_length/pitch)-2,math.ceil(normal_length/pitch)+3):
        n = (k-phase)*pitch
        if settings["axis"] == "vertical":
            def coordinate(y):
                x = bleed+(n-math.sin(tilt)*(y-bleed))/math.cos(tilt)
                return w-x if settings["mirror"] else x
            x0,x2,xh2,xh = (coordinate(y) for y in (0,2,h-2,h))
            if 0 <= x0 <= w or 0 <= xh <= w:
                paths.append(f'<path d="M{x0:.6f},0 L{x2:.6f},2 M{xh2:.6f},{h-2} L{xh:.6f},{h}"/>')
        else:
            def coordinate(x):
                if settings["mirror"]:
                    x=w-x
                return bleed+(n-math.sin(tilt)*(x-bleed))/math.cos(tilt)
            y0,y2,yw2,yw = (coordinate(x) for x in (0,2,w-2,w))
            if 0 <= y0 <= h or 0 <= yw <= h:
                paths.append(f'<path d="M0,{y0:.6f} L2,{y2:.6f} M{w-2},{yw2:.6f} L{w},{yw:.6f}"/>')
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}"><g fill="none" stroke="black" stroke-width="0.05">'+''.join(paths)+'</g></svg>'
    (Path(output)/"registration.svg").write_text(svg, encoding="utf-8")


def write_matrix_template(output,settings):
    (Path(output)/"lens-response-template.json").write_text(json.dumps({
        "matrix":np.eye(settings["ne"]).tolist(),"template_only":True,
        "rows":"observed view angle","columns":"emitted print channel",
        "instruction":"Bu kimlik matrisi ölçüm değildir. Her baskı kanalını ayrı beyaz, diğer kanalları siyah yapıp lens altında sabit pozlamayla ölçün; arka planı çıkarılmış, negatif olmayan kanal yanıtlarını girin. Uygulama her satırı normalize eder."},indent=2,ensure_ascii=False),encoding="utf-8")


def crosstalk_chart(output,settings,transform,profile,font):
    ppi, ne = settings["ppi"],settings["ne"]
    pattern_width,label_width = round(settings["width_mm"]*ppi/25.4),round(22*ppi/25.4)
    band,header = round(10*ppi/25.4),round(13*ppi/25.4)
    width,height = pattern_width+label_width,header+ne*band
    if width*height>150_000_000:
        # Separate full-size TIFF pages keep large calibration jobs bounded in memory.
        pages = True
    else:
        pages = False
    chart = None if pages else Image.new("RGB",(width,height),"white")
    if chart:
        ImageDraw.Draw(chart).text((5,5),"CHANNEL RESPONSE | FIXED EXPOSURE",font=font,fill="black")
    target=Path(output)/"lens-response-test.tif"
    writer = tifffile.TiffWriter(target) if pages else None
    try:
        for emitted in range(ne):
            start = header+emitted*band
            pattern = np.broadcast_to(channel_pattern(width,start,band,settings | {"axis":"vertical","mirror":False}),(band,width))
            pixels = np.where(pattern == emitted,255,0).astype(np.uint8)
            image = Image.fromarray(pixels).convert("RGB")
            ImageDraw.Draw(image).rectangle((0,0,label_width-1,band),fill="white")
            ImageDraw.Draw(image).text((3,3),f"CHANNEL {emitted}",font=font,fill="black")
            if pages:
                if settings["axis"] == "horizontal":image=image.transpose(Image.Transpose.TRANSPOSE)
                if settings["mirror"]:image=image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                rendered=np.asarray(ImageCms.applyTransform(image,transform))
                writer.write(rendered,photometric="separated" if settings["color_mode"] == "CMYK" else "rgb",
                    resolution=(ppi,ppi),resolutionunit="INCH",metadata=None,
                    extratags=[(34675,"B",len(profile),profile,False)])
            else:
                chart.paste(image,(0,start))
    finally:
        if writer:writer.close()
    if chart:
        if settings["axis"] == "horizontal":chart=chart.transpose(Image.Transpose.TRANSPOSE)
        if settings["mirror"]:chart=chart.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        ImageCms.applyTransform(chart,transform).save(target,dpi=(ppi,ppi),compression="tiff_lzw",icc_profile=profile)


def proof(render_folder, output, settings, indices, mixing, inverse):
    frames = []
    proof_ppi = 640*25.4/max(settings["width_mm"]+2*settings["bleed_mm"],settings["height_mm"]+2*settings["bleed_mm"])
    proof_settings = settings | {"ppi":proof_ppi,"mirror":False}
    proof_w = round((settings["width_mm"]+2*settings["bleed_mm"])*proof_ppi/25.4)
    proof_h = round((settings["height_mm"]+2*settings["bleed_mm"])*proof_ppi/25.4)
    for index in indices:
        with Image.open(Path(render_folder)/f"views/view_{index:04d}.png") as im:
            im = im.convert("RGBA")
            bg = Image.new("RGBA", im.size, "white")
            bg.alpha_composite(im)
            im = bg.convert("RGB")
            frames.append(fitted_tile(np.asarray(im),proof_w,proof_h,0,proof_h,proof_settings))
    frames = np.stack(frames)
    values = to_linear(frames)
    adjusted,_,_ = compensated_frames(frames,inverse,settings["gamut_guard"])
    compensated = to_linear(from_linear(adjusted))
    before = np.einsum('ij,jhwc->ihwc',mixing,values,optimize=True)
    after = np.einsum('ij,jhwc->ihwc',mixing,compensated,optimize=True)
    simulated = from_linear(after)
    errors = dict(before_mse=float(np.mean((before-values)**2)),after_mse=float(np.mean((after-values)**2)),
        basis="linear-light preview using the selected mixing matrix; excludes lens/raster alignment, ICC and physical printer behavior")
    # Same view and framing, so correction can be inspected without rerendering.
    panels = []
    middle = len(frames)//2
    for pixels,label in ((frames[middle],"Hedef"),(from_linear(before[middle]),"Telafisiz"),(simulated[middle],"Telafili")):
        im = Image.fromarray(pixels)
        im.thumbnail((240,240))
        panel = Image.new("RGB",(240,270),"#141a23")
        panel.paste(im,((240-im.width)//2,27+(240-im.height)//2))
        ImageDraw.Draw(panel).text((10,8),label,fill="white")
        panels.append(panel)
    comparison = Image.new("RGB",(720,270))
    for i,panel in enumerate(panels):
        comparison.paste(panel,(240*i,0))
    comparison.save(Path(output)/"ghosting-comparison.png")
    proof_folder = Path(output)/"proof"
    proof_folder.mkdir()
    images = [Image.fromarray(frame) for frame in simulated]
    for index, frame in enumerate(images):
        frame.save(proof_folder/f"view_{index:04d}.png")
    sequence = images+images[-2:0:-1]
    sequence[0].save(Path(output)/"lens-proof.png", save_all=True, append_images=sequence[1:],
        duration=max(40, round(2000/(len(images)-1))), loop=0, disposal=0, blend=0)
    with Image.open(Path(render_folder)/"center.png") as im:
        im = im.convert("RGB")
        im.thumbnail((700,700))
        im.save(Path(output)/"preview.png")
    return errors
