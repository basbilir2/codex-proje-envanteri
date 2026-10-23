import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import subprocess

import numpy as np
from PIL import Image

from .geometry import build_mesh, read_depth, validate


def find_blender(explicit=None):
    candidates = [explicit, os.environ.get("BLENDER_PATH"), shutil.which("blender")]
    for root in (Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Blender Foundation",
                 Path.home() / "scoop/apps/blender/current"):
        if root.is_dir():
            candidates += sorted(root.glob("*/blender.exe"), reverse=True) + list(root.glob("blender.exe"))
    for value in candidates:
        if value and Path(value).is_file():
            return Path(value).resolve()
    raise ValueError("Blender bulunamadı. --blender ile blender.exe yolunu belirtin.")


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() if hasattr(hashlib, "file_digest") else hashlib.sha256(stream.read()).hexdigest()


def render(photo, depth_path, output, config, blender=None, repair=None, progress=None):
    config = validate(config)
    photo, depth_path, output = Path(photo).resolve(), Path(depth_path).resolve(), Path(output).resolve()
    blender = find_blender(blender)
    if not photo.is_file() or not depth_path.is_file():
        raise ValueError("Fotoğraf veya depth dosyası bulunamadı.")
    # Never write a job into synced references or a directory containing the inputs.
    if "sources" in (part.lower() for part in output.parts):
        raise ValueError("Çıktı sources altında olamaz.")
    if output == photo.parent or output == depth_path.parent:
        raise ValueError("Çıktı için giriş dosyalarından ayrı bir klasör kullanın.")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Çıktı klasörü dolu. Yeni bir klasör adı kullanın.")
    with Image.open(photo) as image:
        if image.getexif().get(274, 1) != 1:
            raise ValueError("Fotoğraf EXIF dönüşü içeriyor. Fotoğrafı ve depth'i aynı yönde kaydedin.")
        source = image.convert("RGBA")
    depth = read_depth(depth_path, source.size, config["depth_convention"])
    mesh, stats = build_mesh(depth, config)
    if not stats["triangles"]:
        raise ValueError("Depth sınır eşiği ile hiçbir yüzey oluşmadı.")
    version = subprocess.run([str(blender), "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    job = dict(schema_version=1, stage="supplied_depth_blender_preview", config=config,
               size=source.size, blender_version=version, mesh=stats,
               source_inputs={"photo":str(photo), "depth":str(depth_path),
                              "photo_sha256":digest(photo), "depth_sha256":digest(depth_path)},
               coordinate_convention="X right, Y up, camera looks -Z; positive endpoint disparity is behind",
               limitations=["No hidden surface reconstruction", "No lens calibration or interlacing",
                            "Ne is metadata only; Nr controls rendering", "Scene lengths are virtual units"])
    output.mkdir(parents=True, exist_ok=True)
    source.save(output / "source.png")
    np.save(output / "depth_proximity.npy", depth, allow_pickle=False)
    np.savez_compressed(output / "mesh.npz", **mesh)
    if repair and repair.get("enabled", True):
        from .layers import layered_surfaces
        job["surfaces"],job["mesh"] = layered_surfaces(source, depth, output, config,
            count=int(repair.get("layers", 3)), radius=float(repair.get("radius", 5)))
        job["limitations"][0] = "Separate alpha/depth layers; hidden background is estimated with Telea inpainting"
    job_path = output / "job.json"
    job_path.write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")
    script = Path(__file__).with_name("blender_scene.py")
    command = [str(blender), "--background", "--factory-startup", "--python-exit-code", "1", "--python", str(script), "--", str(job_path)]
    with (output / "blender.log").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, encoding="utf-8", errors="replace")
        try:
            for line in process.stdout:
                log.write(line)
                if line.startswith("LENTICULAR_VIEW"):
                    print(line.strip(), flush=True)
                    if progress:
                        progress(line.strip())
            code = process.wait()
        except BaseException:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            raise
    if code:
        raise RuntimeError(f"Blender başarısız ({code}). Ayrıntı: {output / 'blender.log'}")
    preview(output, job)
    return output


def preview(output, job):
    frames, coverage = [], []
    for index in range(job["config"]["nr"]):
        with Image.open(output / f"views/view_{index:04d}.png") as image:
            frame = image.convert("RGBA")
        coverage.append(float(np.mean(np.asarray(frame.getchannel("A")) < 250)))
        frame.thumbnail((960, 960))
        frames.append(frame)
    sequence = frames + frames[-2:0:-1]
    duration = round(job["config"]["sweep_seconds"] * 1000 / (len(frames) - 1))
    sequence[0].save(output / "look-around.png", save_all=True, append_images=sequence[1:],
                     duration=duration, loop=0, disposal=0, blend=0)
    coverage_report = dict(nonopaque_fraction_per_view=coverage, max_nonopaque_fraction=max(coverage),
                           note="Includes disocclusions, outer boundaries and source transparency; not a reconstruction score.")
    (output / "coverage.json").write_text(json.dumps(coverage_report, indent=2), encoding="utf-8")
    labels = json.dumps([f"views/view_{i:04d}.png" for i in range(len(frames))])
    title = html.escape(f"Lenticular başlangıç önizlemesi — Nr={len(frames)} / Ne={job['config']['ne']}")
    document = """<!doctype html><html lang="tr"><meta charset="utf-8"><title>Look-around</title>
<style>body{font:16px system-ui;background:#202329;color:#eee;max-width:1100px;margin:24px auto;padding:0 16px}
img{display:block;max-width:100%;max-height:75vh;margin:auto;background:repeating-conic-gradient(#888 0 25%,#bbb 0 50%) 0/20px 20px}
button,input{margin:12px 8px 12px 0}input{width:60%}</style>
<h1>TITLE</h1><p>Damalı alanlar görünmeyen veya şeffaf bölgeleri gösterir. Bu, ideal sahne önizlemesidir.</p>
<img id="image" src="views/view_0000.png" alt="2.5D görünüş">
<button id="play">Oynat</button><input id="slider" type="range" min="0" max="MAX" value="0" step="1"><span id="label"></span>
<script>const files=FILES, slider=document.getElementById('slider'), image=document.getElementById('image'),
label=document.getElementById('label'), button=document.getElementById('play');let timer=null,i=0,d=1;
files.forEach(src=>{const preload=new Image();preload.src=src});
function show(n){i=n;slider.value=n;image.src=files[n];label.textContent=(n+1)+' / '+files.length}
slider.oninput=()=>{stop();show(Number(slider.value))};
function stop(){clearInterval(timer);timer=null;button.textContent='Oynat'}
button.onclick=()=>{if(timer){stop();return}button.textContent='Durdur';timer=setInterval(()=>{
if(i===files.length-1)d=-1;if(i===0)d=1;show(i+d)},DELAY)};show(0);</script></html>"""
    document = document.replace("TITLE", title).replace("MAX", str(len(frames)-1)).replace("FILES", labels).replace("DELAY", str(duration))
    (output / "preview.html").write_text(document, encoding="utf-8")
