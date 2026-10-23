"""Common disk-backed frame sources for camera views and timed effects."""
import json
import hashlib
from collections import OrderedDict
from pathlib import Path

import numpy as np
from PIL import Image

from .runner import digest


class FrameSet:
    def __init__(self, folder):
        self.folder = Path(folder).resolve()
        path = self.folder / 'frameset.json'
        self.legacy = not path.is_file()
        if self.legacy:
            path = self.folder / 'job.json'
            job = json.loads(path.read_text(encoding='utf-8'))
            cfg = job['config']
            positions = np.asarray(cfg['positions'], dtype=float)
            if len(positions) != cfg['nr'] or not np.isfinite(positions).all() or cfg['zero'] <= 0:
                raise ValueError('Kamera görünüş bilgisi geçersiz.')
            self.data = dict(schema_version=1, kind='multiview_3d', ns=1,
                engine='Blender', config=cfg, legacy_job=job,
                frames=[dict(path=f'views/view_{i:04d}.png', view_coordinate=float(a), generated=True)
                        for i, a in enumerate(np.arctan(positions/cfg['zero']))])
        else:
            self.data = json.loads(path.read_text(encoding='utf-8'))
        self.manifest_path = path
        if self.data.get('schema_version') != 1 or self.data.get('kind') not in ('multiview_3d', 'time_sequence'):
            raise ValueError('Kare seti türü veya sürümü desteklenmiyor.')
        self.records = self.data.get('frames', [])
        if not 2 <= len(self.records) <= 1024:
            raise ValueError('Kare seti 2–1024 kare içermeli.')
        key = 'view_coordinate' if self.kind == 'multiview_3d' else 'time_s'
        coordinates = [r.get(key) for r in self.records]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not np.isfinite(v) for v in coordinates):
            raise ValueError('Kare zamanları/açıları sonlu sayılar olmalı.')
        if any(b <= a for a, b in zip(coordinates, coordinates[1:])):
            raise ValueError('Kare zamanları/açıları artan sırada olmalı.')
        self.size = None
        for record in self.records:
            filename = record.get('path')
            if not isinstance(filename, str):
                raise ValueError('Kare yolu geçersiz.')
            target = (self.folder/filename).resolve()
            if not target.is_relative_to(self.folder) or not target.is_file():
                raise ValueError('Kare dosyası eksik veya çalışma klasörü dışında.')
            with Image.open(target) as image:
                if self.size is None:
                    self.size = image.size
                if image.size != self.size:
                    raise ValueError('Bütün kareler aynı tuval boyutunda olmalı.')
            if not self.legacy and record.get('sha256') != digest(target):
                raise ValueError('Kare dosyası kayıtlı hash ile uyuşmuyor.')
        if not self.legacy and list(self.size) != self.data.get('size'):
            raise ValueError('Kare boyutu manifest ile uyuşmuyor.')

    @property
    def kind(self):
        return self.data['kind']

    def image(self, index):
        with Image.open(self.folder/self.records[index]['path']) as image:
            return image.convert('RGBA')

    def plan(self, settings):
        ne = settings['ne']
        key = 'view_coordinate' if self.kind == 'multiview_3d' else 'time_s'
        coords = np.array([r[key] for r in self.records])
        if self.data.get('mode') == 'flip':
            weights = np.array(self.data.get('weights', [1]*len(coords)), dtype=float)
            if len(weights) != len(coords) or not np.isfinite(weights).all() or np.any(weights <= 0):
                raise ValueError('Flip bekleme payları pozitif ve kare sayısıyla eşit olmalı.')
            indices = np.searchsorted(np.cumsum(weights/weights.sum()), (np.arange(ne)+.5)/ne).tolist()
        else:
            targets = np.linspace(coords[0], coords[-1], ne)
            indices = np.abs(coords[:, None]-targets[None, :]).argmin(0).tolist()
        # A convex lenticule sends its left strip to the right observer.
        # Camera X grows rightwards, unlike raster rows and camera Y (upwards).
        optical_reverse = self.kind == 'multiview_3d' and self.data.get('config', {}).get('camera_axis', 'x') == 'x'
        if optical_reverse != settings['reverse_views']:
            indices.reverse()
        return dict(schema_version=1, kind=self.kind, ne=ne, source_indices=indices,
            ordering_version=2, orthoscopic=self.kind == 'multiview_3d' and not settings['reverse_views'],
            order_basis='convex lenticule; X right, Y up; raster columns right, rows down',
            samples=[dict(channel=j, frame_index=i, **{key:float(coords[i])}) for j, i in enumerate(indices)],
            unused_frames=sorted(set(range(len(coords)))-set(indices)), repeated_channels=ne-len(set(indices)))


class FrameProvider:
    """Byte-budgeted source cache; output raster tiles remain streamed."""
    def __init__(self, frameset, indices, allow_unfilled):
        self.frameset, self.cache = frameset, OrderedDict()
        self.cache_bytes = 0
        # Twelve native portrait views slightly exceed 128 MiB. Keep that working
        # set when it fits 256 MiB, rather than decoding every PNG for every strip.
        required = len(set(indices))*frameset.size[0]*frameset.size[1]*3
        self.cache_budget = max(128*1024*1024,min(256*1024*1024,required))
        self.missing = 0.
        self.pixel_hashes = set()
        for index in set(indices):
            rgba = np.asarray(frameset.image(index))
            self.pixel_hashes.add(hashlib.sha256(rgba.data).hexdigest())
            self.missing = max(self.missing, float(np.mean(rgba[:, :, 3] < 250)))
        if self.missing > .0005 and not allow_unfilled:
            raise ValueError(f'Karelerde %{self.missing*100:.2f} boş alan var. Doldurun veya taslak boş alan izni seçin.')

    def __getitem__(self, index):
        if index not in self.cache:
            rgba = np.asarray(self.frameset.image(index))
            alpha = rgba[:, :, 3:4].astype(np.float32)/255
            self.cache[index] = np.rint(rgba[:, :, :3]*alpha+255*(1-alpha)).astype(np.uint8)
            self.cache_bytes += self.cache[index].nbytes
            while self.cache_bytes > self.cache_budget and len(self.cache) > 1:
                _,old = self.cache.popitem(last=False)
                self.cache_bytes -= old.nbytes
        self.cache.move_to_end(index)
        return self.cache[index]

    def values(self):
        yield self[0]
