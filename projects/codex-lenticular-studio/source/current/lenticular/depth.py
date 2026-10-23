"""Local, single-image DA3MONO inference; relative depth is not metric depth."""
import importlib.metadata
import json
from pathlib import Path
import shutil
import time
import urllib.request

import numpy as np
from PIL import Image

from .runner import digest


MODEL_ID = "depth-anything/DA3MONO-LARGE"
MODEL_REVISION = "f465978e618db8cc79c83b8bbf24964857db1875"
UPSTREAM_COMMIT = "3d835ec1a5802d64a8b8b15f817a1ab54809bfe4"
ARTIFACTS = {
    "config.json": (845, "649809acdfe99631293430bfb8bcd85620a1bba47bb4e27689bd204c645a4204"),
    "model.safetensors": (1336734448, "7a799a7f95eb8d4c404c2ca8be3dc3276b350a417ddc4420db72ba850cc0e960"),
}


def proximity_from_depth(depth, normalization="preserve"):
    """Invert direct relative Z, then map robust bounds to white-near [0, 1]."""
    depth = np.asarray(depth, dtype=np.float32)
    if depth.ndim != 2 or not depth.size or not np.isfinite(depth).all() or np.any(depth <= 0):
        raise ValueError("Model depth çıktısı iki boyutlu, sonlu ve pozitif olmalı.")
    inverse = 1.0 / depth
    if not np.isfinite(inverse).all():
        raise ValueError("Model depth değerleri ters derinlik için çok küçük.")
    if normalization not in ("preserve", "robust"):
        raise ValueError("Derinlik dağılımı preserve veya robust olmalı.")
    percentiles = [0,100] if normalization == "preserve" else [1,99]
    low, high = np.percentile(inverse, percentiles)
    if high - low <= max(abs(high), abs(low), 1e-12) * 1e-6:
        raise ValueError("Model anlamlı bir derinlik aralığı üretmedi.")
    proximity = np.clip((inverse - low) / (high - low), 0, 1).astype(np.float32)
    return proximity, {"normalization":normalization,"inverse_depth_percentiles": percentiles,
                       "inverse_depth_bounds": [float(low), float(high)],
                       "clipped_fraction": float(np.mean((inverse < low) | (inverse > high)))}


def check_destination(folder):
    folder = Path(folder).resolve()
    if "sources" in (part.lower() for part in folder.parts):
        raise ValueError("Depth veya model önbelleği sources altında olamaz.")
    return folder


def model_file(cache, name):
    """Fetch immutable official artifacts with size and upstream SHA-256 checks."""
    folder = check_destination(Path(cache) / "DA3MONO-LARGE" / MODEL_REVISION)
    path = folder / name
    size, expected_hash = ARTIFACTS[name]
    if path.exists():
        if path.stat().st_size != size or digest(path) != expected_hash:
            raise RuntimeError(f"Model önbelleği hash kontrolünü geçemedi: {path}")
        return path
    folder.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + ".download")
    url = f"https://huggingface.co/{MODEL_ID}/resolve/{MODEL_REVISION}/{name}"
    received, next_report = 0, 64 * 1024 * 1024
    # Standard HTTPS works on Windows without Xet workers, symlinks or a login.
    with urllib.request.urlopen(url, timeout=30) as response, partial.open("wb") as stream:
        while chunk := response.read(4 * 1024 * 1024):
            stream.write(chunk)
            received += len(chunk)
            if received >= next_report:
                print(f"DEPTH indirme: {100 * received / size:.0f}%", flush=True)
                next_report += 64 * 1024 * 1024
    if received != size or digest(partial) != expected_hash:
        raise RuntimeError(f"Model indirme boyutu veya hash'i yanlış: {partial}")
    partial.replace(path)
    return path


def load_mono_model(cache=None):
    cache = check_destination(cache or Path(__file__).resolve().parents[1] / ".models")
    try:
        import torch
        from safetensors.torch import load_file
        from depth_anything_3.cfg import create_object
    except ImportError as error:
        raise RuntimeError("AI depth ortamı eksik. Önce .\\setup-depth.ps1 çalıştırın.") from error

    # Load the official mono core directly: export/Gaussian dependencies are unnecessary.
    # Fixed repository/revision; no remote Python config or pickle checkpoint is executed.
    print("DEPTH: DA3MONO-LARGE ağırlıkları yerel önbelleğe alınıyor...", flush=True)
    files = {name: model_file(cache, name) for name in ARTIFACTS}
    settings = json.loads(files["config.json"].read_text(encoding="utf-8"))
    if settings.get("model_name") != "da3mono-large":
        raise RuntimeError("Beklenmeyen model yapılandırması.")
    torch.set_num_threads(min(8, torch.get_num_threads()))
    model = create_object(settings["config"])
    state = load_file(str(files["model.safetensors"]), device="cpu")
    if not all(key.startswith("model.") for key in state):
        raise RuntimeError("Beklenmeyen checkpoint anahtarları.")
    model.load_state_dict({key.removeprefix("model."): value for key, value in state.items()}, strict=True)
    del state
    model.eval()
    return model


def predict_depth(image, model, process_res=504):
    import torch
    from depth_anything_3.utils.io.input_processor import InputProcessor
    tensor, _, _ = InputProcessor()([image], process_res=process_res,
                                   process_res_method="upper_bound_resize", sequential=True)
    with torch.inference_mode():
        prediction = model(tensor.unsqueeze(0))
        raw = prediction["depth"].reshape(*tensor.shape[-2:]).float()
        aligned = torch.nn.functional.interpolate(raw[None, None],
                     size=(image.height, image.width), mode="bilinear", align_corners=False)[0, 0].numpy()
    return raw, aligned


def estimate(photo, output, cache=None, process_res=504):
    photo, output = Path(photo).resolve(), check_destination(output)
    cache = check_destination(cache or Path(__file__).resolve().parents[1] / ".models")
    if output.exists() and any(output.iterdir()):
        raise ValueError("Depth çıktı klasörü dolu; yeni bir klasör kullanın.")
    if not isinstance(process_res, int) or not 140 <= process_res <= 1008:
        raise ValueError("Model çözünürlüğü 140–1008 arasında olmalı.")
    with Image.open(photo) as original:
        if original.getexif().get(274, 1) != 1:
            raise ValueError("Fotoğrafı EXIF dönüşü uygulanmış olarak kaydedin.")
        image = original.convert("RGB")
        texture = original.convert("RGBA")
    source_hash = digest(photo)
    import torch
    started = time.perf_counter()
    model = load_mono_model(cache)
    print("DEPTH: fotoğraf bilgisayarda işleniyor (CPU)...", flush=True)
    infer_started = time.perf_counter()
    raw, aligned = predict_depth(image,model,process_res)
    inference_seconds = time.perf_counter() - infer_started
    proximity, normalization = proximity_from_depth(aligned)
    output.mkdir(parents=True, exist_ok=True)
    original_copy = output / ("original" + photo.suffix.lower())
    shutil.copyfile(photo, original_copy)
    if digest(original_copy) != source_hash or digest(photo) != source_hash:
        raise RuntimeError("Kaynak fotoğraf hash kontrolü başarısız.")
    texture.save(output / "photo.png")
    np.save(output / "raw_model_depth.npy", raw.numpy(), allow_pickle=False)
    np.save(output / "relative_depth.npy", aligned, allow_pickle=False)
    np.save(output / "depth_proximity.npy", proximity, allow_pickle=False)
    Image.fromarray(np.rint(proximity * 65535).astype(np.uint16)).save(output / "depth.png")
    Image.fromarray(np.rint(proximity * 255).astype(np.uint8)).save(output / "depth_preview.png")
    metadata = dict(schema_version=1, model_id=MODEL_ID, model_revision=MODEL_REVISION,
                    upstream_commit=UPSTREAM_COMMIT, license="Apache-2.0", device="cpu",
                    torch_version=torch.__version__, model_sha256=ARTIFACTS["model.safetensors"][1],
                    upstream_version=importlib.metadata.version("depth-anything-3"),
                    source_photo=str(photo), source_sha256=source_hash,
                    size=list(image.size), model_size=list(reversed(raw.shape)),
                    process_res=process_res, process_res_method="upper_bound_resize",
                    alignment="full-frame bilinear resize, no crop, align_corners=False",
                    model_semantics="direct relative depth Z, not disparity and not metres",
                    output_convention="white-near inverse relative depth normalized to [0,1]",
                    normalization=normalization, inference_seconds=inference_seconds,
                    elapsed_seconds=time.perf_counter() - started,
                    limitations=["Single-image estimated depth, not measured geometry",
                                 "Veil, hair, petals and occluded boundaries can be wrong",
                                 "No segmentation, inpainting or hidden surface generation"])
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"DEPTH tamamlandı: {inference_seconds:.1f} saniye", flush=True)
    return output / "photo.png", output / "depth_proximity.npy"
