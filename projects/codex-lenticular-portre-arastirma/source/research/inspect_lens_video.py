"""Read-only sampling of the user's physical lenticular-print video."""
from pathlib import Path
import hashlib
import json
import cv2
from PIL import Image, ImageDraw, ImageFont

SOURCE = Path(r'C:\Users\USER\Downloads\WhatsApp Video 2026-10-09 at 15.52.16.mp4')
OUT = Path(__file__).resolve().parent / 'video-review-20261009-155216'

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    before = digest(SOURCE)
    cap = cv2.VideoCapture(str(SOURCE))
    assert cap.isOpened()
    fps = cap.get(cv2.CAP_PROP_FPS)
    count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = count / fps
    OUT.mkdir(exist_ok=False)
    font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 20)
    sheet = Image.new('RGB', (4 * 244, 4 * 450), '#eeeeee')
    draw = ImageDraw.Draw(sheet)
    samples = []
    for i in range(16):
        index = min(count - 1, round(i * fps))
        cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = cap.read()
        assert ok, index
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb)
        path = OUT / f'frame-{i:02d}s.png'
        image.save(path)
        image.thumbnail((232, 416))
        x, y = (i % 4) * 244 + 6, (i // 4) * 450 + 28
        sheet.paste(image, (x, y))
        draw.text((x, y - 25), f'{index/fps:.2f} s', font=font, fill='black')
        samples.append({'frame': index, 'seconds': index / fps, 'file': str(path)})
    cap.release()
    sheet.save(OUT / 'contact-sheet.jpg', quality=95)
    assert digest(SOURCE) == before
    report = dict(source=str(SOURCE), sha256=before, frames=count, fps=fps,
                  duration_seconds=duration, size=[464, 832], samples=samples,
                  limitation='A monocular compressed phone video cannot verify binocular depth or isolate printing blur.')
    (OUT / 'video-inspection.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(OUT), 'duration_seconds': duration, 'source_unchanged': True}))

if __name__ == '__main__':
    main()
