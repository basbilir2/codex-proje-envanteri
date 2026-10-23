"""Camera and mesh math independent of Blender. All scene lengths use virtual units."""
import math

import numpy as np
from PIL import Image


def validate(config):
    if not isinstance(config, dict):
        raise ValueError("Ayar dosyası bir JSON nesnesi olmalı.")
    defaults = dict(nr=12, ne=None, near=1.5, far=3.0, zero=2.0,
                    focal_mm=50.0, sensor_width_mm=36.0, camera_span=0.06,
                    positions=None, grid_size=256, edge_threshold=0.1,
                    depth_convention="white-near", sweep_seconds=2.0, camera_axis="x",edge_mode="cut")
    unknown = set(config) - set(defaults)
    if unknown:
        raise ValueError(f"Bilinmeyen ayarlar: {', '.join(sorted(unknown))}")
    result = defaults | config
    for key in ("nr", "grid_size"):
        if type(result[key]) is not int:
            raise ValueError(f"{key} tam sayı olmalı.")
    if not 2 <= result["nr"] <= 1024:
        raise ValueError("Nr 2–1024 arasında olmalı.")
    if result["ne"] is not None and (type(result["ne"]) is not int or result["ne"] < 2):
        raise ValueError("Ne boş veya en az 2 olan tam sayı olmalı; bu aşamada kullanılmaz.")
    if not 2 <= result["grid_size"] <= 2048:
        raise ValueError("grid_size 2–2048 arasında olmalı.")
    for key in ("near", "far", "zero", "focal_mm", "sensor_width_mm", "camera_span", "edge_threshold", "sweep_seconds"):
        if isinstance(result[key], bool) or not isinstance(result[key], (int, float)) or not math.isfinite(result[key]):
            raise ValueError(f"{key} sonlu sayı olmalı.")
    if not 0 < result["near"] < result["far"] or result["zero"] <= 0:
        raise ValueError("0 < near < far ve zero > 0 olmalı.")
    if min(result["focal_mm"], result["sensor_width_mm"], result["sweep_seconds"]) <= 0 or result["camera_span"] < 0:
        raise ValueError("Odak/sensör/süre pozitif, kamera açıklığı negatif olmayan sayı olmalı.")
    if not 0 <= result["edge_threshold"] <= 1:
        raise ValueError("edge_threshold 0–1 arasında olmalı.")
    if result["depth_convention"] not in ("white-near", "black-near"):
        raise ValueError("depth_convention white-near veya black-near olmalı.")
    if result["camera_axis"] not in ("x","y"):
        raise ValueError("camera_axis x veya y olmalı.")
    if result["edge_mode"] not in ("cut","split"):
        raise ValueError("edge_mode cut veya split olmalı.")
    if result["positions"] is None:
        positions = np.linspace(-result["camera_span"] / 2, result["camera_span"] / 2, result["nr"])
    else:
        positions = np.asarray(result["positions"], dtype=float)
        if positions.shape != (result["nr"],) or not np.isfinite(positions).all() or not np.all(np.diff(positions) > 0):
            raise ValueError("positions, Nr adet sonlu ve soldan sağa artan kamera konumu içermeli.")
    result["positions"] = positions.tolist()
    return result


def read_depth(path, size, convention):
    """PNG/TIFF grayscale uses full integer range. NPY must already be [0,1]."""
    if path.suffix.lower() == ".npy":
        depth = np.load(path, allow_pickle=False)
    else:
        with Image.open(path) as image:
            if image.mode not in ("L", "I", "I;16", "I;16L", "I;16B", "F"):
                raise ValueError("Depth tek kanallı gri PNG/TIFF veya [0,1] NPY olmalı.")
            array = np.asarray(image)
            if np.issubdtype(array.dtype, np.integer):
                limit = 255 if image.mode == "L" else 65535
                depth = array.astype(np.float32) / limit
            else:
                depth = array.astype(np.float32)
    depth = np.asarray(depth, dtype=np.float32)
    if depth.shape != (size[1], size[0]):
        raise ValueError("Fotoğraf ve depth boyutları aynı olmalı; otomatik hizalama/ölçekleme yapılmaz.")
    if not np.isfinite(depth).all() or depth.min() < 0 or depth.max() > 1:
        raise ValueError("Depth değerleri sonlu ve [0,1] aralığında olmalı.")
    return 1 - depth if convention == "black-near" else depth


def build_mesh(depth, config, padding=0):
    height, width = depth.shape
    # Pixel-edge geometry fills the original camera frame; texture UVs stay registered.
    count_x = min(width + 1, config["grid_size"] + 1)
    count_y = min(height + 1, max(2, round(config["grid_size"] * height / width) + 1))
    u, v = np.meshgrid(np.linspace(-padding, width+padding, count_x), np.linspace(-padding, height+padding, count_y))
    ix = np.clip(np.rint(u - 0.5).astype(int), 0, width - 1)
    iy = np.clip(np.rint(v - 0.5).astype(int), 0, height - 1)
    proximity = depth[iy, ix]
    # Linear inverse-depth mapping gives controlled, linear disparity in proximity.
    z = 1 / ((1 - proximity) / config["far"] + proximity / config["near"])
    focal_px = width * config["focal_mm"] / config["sensor_width_mm"]
    vertices = np.stack(((u - width / 2) * z / focal_px,
                         (height / 2 - v) * z / focal_px, -z), axis=-1).reshape(-1, 3)
    uv = np.stack((u / width, 1 - v / height), axis=-1).reshape(-1, 2)
    index = np.arange(count_x * count_y).reshape(count_y, count_x)
    a, b, c, d = index[:-1, :-1], index[:-1, 1:], index[1:, :-1], index[1:, 1:]
    flat = proximity.reshape(-1)
    use_ad = np.abs(flat[a]-flat[d]) < np.abs(flat[b]-flat[c])
    # Follow the smoother diagonal so silhouette corners lose fewer valid faces.
    first = np.where(use_ad[...,None],np.stack((a,c,d),-1),np.stack((a,c,b),-1))
    second = np.where(use_ad[...,None],np.stack((a,d,b),-1),np.stack((b,c,d),-1))
    triangles = np.concatenate((first.reshape(-1,3),second.reshape(-1,3)))
    values = proximity.reshape(-1)[triangles]
    keep = np.ptp(values, axis=1) <= config["edge_threshold"]
    split_count = 0
    selected = triangles[keep]
    if config.get("edge_mode","cut") == "split" and np.any(~keep):
        # Fill each discontinuous triangle at its median depth on its own vertices.
        # Its UV footprint stays exact at the source camera, with no bridge across the depth jump.
        fragments = vertices[triangles[~keep]]
        distances = -fragments[:,:,2]
        flat_depth = np.median(distances,axis=1)
        fragments = fragments/distances[:,:,None]*flat_depth[:,None,None]
        offset = len(vertices)
        selected = np.concatenate((selected,np.arange(offset,offset+fragments.size//3).reshape(-1,3)))
        uv = np.concatenate((uv,uv[triangles[~keep]].reshape(-1,2)))
        vertices = np.concatenate((vertices,fragments.reshape(-1,3)))
        split_count = int((~keep).sum())
    return dict(vertices=vertices.astype(np.float32), uv=uv.astype(np.float32),
                triangles=selected.astype(np.int32)), dict(
                    vertices=len(vertices), triangles=len(selected),split_triangles=split_count,
                    cut_triangles=int((~keep).sum())-split_count, focal_px=focal_px)


def shift_x(position, config):
    # HORIZONTAL sensor fit: positive shift moves principal point left.
    return -config["focal_mm"] * position / (config["sensor_width_mm"] * config["zero"])
