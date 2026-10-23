import argparse
import json
from pathlib import Path
import subprocess
import sys

from .runner import find_blender, render


def demo_inputs(folder):
    import numpy as np
    from PIL import Image, ImageDraw
    folder = Path(folder).resolve()
    if "sources" in (part.lower() for part in folder.parts):
        raise ValueError("Demo sources altında oluşturulamaz.")
    if folder.exists() and any(folder.iterdir()):
        raise ValueError("Demo klasörü dolu; yeni klasör kullanın.")
    folder.mkdir(parents=True, exist_ok=True)
    width, height = 480, 320
    photo = Image.new("RGB", (width, height), (35, 70, 130))
    draw = ImageDraw.Draw(photo)
    draw.rectangle((160, 0, 319, 319), fill=(50, 170, 90))
    draw.rectangle((320, 0, 479, 319), fill=(210, 70, 45))
    for x in (80, 240, 400):
        draw.rectangle((x-5, 35, x+5, 284), fill="white")
        draw.text((x-25, 15), "FAR" if x == 80 else "ZERO" if x == 240 else "NEAR", fill="white")
    depth = np.zeros((height, width), dtype=np.uint16)
    depth[:, 160:320] = 32768  # inverse-depth midpoint maps to Z=2 (16-bit rounding).
    depth[:, 320:] = 65535
    photo.save(folder / "photo.png")
    Image.fromarray(depth).save(folder / "depth.png")
    return folder / "photo.png", folder / "depth.png"


def main():
    parser = argparse.ArgumentParser(description="Fotoğraf / depth / Blender 2.5D görünüşleri")
    sub = parser.add_subparsers(dest="command", required=True)
    studio = sub.add_parser("studio", help="Lenticular Studio ayar ekranını aç")
    studio.add_argument("--port", type=int, default=8765)
    studio.add_argument("--no-browser", action="store_true")
    printing = sub.add_parser("print", help="Blender görünüşlerinden lenticular TIFF hazırla")
    printing.add_argument("--render", required=True)
    printing.add_argument("--config", required=True)
    printing.add_argument("--output", required=True)
    doctor = sub.add_parser("doctor", help="Blender bağlantısını kontrol et")
    doctor.add_argument("--blender")
    run = sub.add_parser("render", help="Hazır girdilerden görünüş üret")
    run.add_argument("--photo", required=True)
    run.add_argument("--depth", required=True)
    run.add_argument("--output", required=True)
    run.add_argument("--config", help="JSON ayarları")
    run.add_argument("--blender")
    auto = sub.add_parser("from-photo", help="Fotoğraftan yerel AI depth ve Blender önizlemesi üret")
    auto.add_argument("--photo", required=True)
    auto.add_argument("--output", required=True)
    auto.add_argument("--config", help="Blender JSON ayarları; depth yönü white-near olmalı")
    auto.add_argument("--blender")
    auto.add_argument("--model-cache")
    auto.add_argument("--process-res", type=int, default=504)
    depth_only = sub.add_parser("depth", help="Yalnız yerel AI depth üret")
    depth_only.add_argument("--photo", required=True)
    depth_only.add_argument("--output", required=True)
    depth_only.add_argument("--model-cache")
    depth_only.add_argument("--process-res", type=int, default=504)
    demo = sub.add_parser("demo", help="Sentetik üç derinlikli örnek üret ve render et")
    demo.add_argument("--output", default="outputs/demo")
    demo.add_argument("--blender")
    demo.add_argument("--nr", type=int, default=12)
    args = parser.parse_args()
    try:
        if args.command == "studio":
            from .studio import main as studio_main
            studio_main(["--port", str(args.port)] + (["--no-browser"] if args.no_browser else []))
        elif args.command == "print":
            from .printing import encode
            config = json.loads(Path(args.config).read_text(encoding="utf-8-sig"))
            result = encode(args.render, args.output, config, progress=print)
            print(f"Tamamlandı: {Path(args.output).resolve() / 'interlaced.tif'}")
        elif args.command == "doctor":
            blender = find_blender(args.blender)
            version = subprocess.run([str(blender), "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
            print(f"Python: {sys.version.split()[0]}\nBlender: {blender}\n{version}")
        elif args.command == "demo":
            output = Path(args.output).resolve()
            photo, depth = demo_inputs(output / "inputs")
            result = render(photo, depth, output / "render", {"nr":args.nr, "grid_size":480}, args.blender)
            print(f"Tamamlandı: {result / 'preview.html'}")
        elif args.command == "depth":
            from .depth import estimate
            _, result = estimate(args.photo, args.output, args.model_cache, args.process_res)
            print(f"Tamamlandı: {result}")
        elif args.command == "from-photo":
            from .depth import check_destination, estimate
            from .geometry import validate
            config = json.loads(Path(args.config).read_text(encoding="utf-8-sig")) if args.config else {}
            config = validate(config)
            if config["depth_convention"] != "white-near":
                raise ValueError("AI depth akışı white-near kullanır.")
            output = check_destination(args.output)
            if output.exists() and any(output.iterdir()):
                raise ValueError("Çıktı klasörü dolu; yeni bir klasör kullanın.")
            find_blender(args.blender)
            photo, depth = estimate(args.photo, output / "depth", args.model_cache, args.process_res)
            result = render(photo, depth, output / "render", config, args.blender)
            print(f"Tamamlandı: {result / 'preview.html'}")
        else:
            config = json.loads(Path(args.config).read_text(encoding="utf-8-sig")) if args.config else {}
            result = render(args.photo, args.depth, args.output, config, args.blender)
            print(f"Tamamlandı: {result / 'preview.html'}")
        return 0
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Hata: {error}", file=sys.stderr)
        return 1
