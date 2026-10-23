"""Editable depth and deterministic hidden-background layers for Blender."""
from pathlib import Path
import json

import numpy as np
from PIL import Image

from .geometry import build_mesh


def editable_depth(depth, settings, photo=None):
    import cv2
    result = np.array(depth, dtype=np.float32, copy=True)
    smooth = float(settings.get("depth_smoothing", 0))
    if not 0 <= smooth <= 1:
        raise ValueError("Derinlik yumuşatma 0–1 arasında olmalı.")
    if smooth:
        filtered = cv2.bilateralFilter(result, 5, 0.06, 3)
        result = (1-smooth)*result + smooth*filtered
    refinement = float(settings.get("edge_refinement", 0))
    if refinement and photo is not None:
        # Joint local filtering respects both color and depth boundaries. It is not matting.
        guide = np.asarray(photo.convert("RGB"), dtype=np.float32)/255
        padded = np.pad(result, 1, mode="edge")
        colors = np.pad(guide, ((1,1),(1,1),(0,0)), mode="edge")
        accum, weights = np.zeros_like(result), np.zeros_like(result)
        h,w = result.shape
        for dy in range(3):
            for dx in range(3):
                neighbor = padded[dy:dy+h,dx:dx+w]
                distance = np.mean((colors[dy:dy+h,dx:dx+w]-guide)**2,axis=2)
                weight = np.exp(-distance/.0128-(neighbor-result)**2/.0072-((dy-1)**2+(dx-1)**2)/2)
                accum += neighbor*weight
                weights += weight
        result = (1-refinement)*result + refinement*accum/weights
    height, width = result.shape
    black,white,gamma=(float(settings.get(k,d)) for k,d in (("depth_black",0),("depth_white",1),("depth_gamma",1)))
    if not all(np.isfinite([black,white,gamma])) or not (0<=black<=.95 and .05<=white<=1 and white-black>=.01-1e-9 and .25<=gamma<=4):
        raise ValueError("Derinlik siyah/beyaz/gri dengesi geçersiz.")
    result=np.power(np.clip((result-black)/(white-black),0,1),1/gamma).astype(np.float32)
    strokes = settings.get("depth_strokes", [])
    if not isinstance(strokes, list) or len(strokes) > 10000:
        raise ValueError("Derinlik fırça verisi geçersiz.")
    for stroke in strokes:
        x, y, radius, value, strength = (float(stroke[key]) for key in ("x", "y", "radius", "value", "strength"))
        if not all(np.isfinite([x, y, radius, value, strength])) or not (0 <= x <= 1 and 0 <= y <= 1 and 0 < radius <= .5 and 0 <= value <= 1 and 0 <= strength <= 1):
            raise ValueError("Derinlik fırça ayarı geçersiz.")
        cx, cy, r = x*(width-1), y*(height-1), radius*max(width, height)
        x0, x1 = max(0, int(cx-r)), min(width, int(cx+r)+2)
        y0, y1 = max(0, int(cy-r)), min(height, int(cy+r)+2)
        yy, xx = np.ogrid[y0:y1, x0:x1]
        weight = np.clip(1 - np.sqrt((xx-cx)**2+(yy-cy)**2)/r, 0, 1)*strength
        region = result[y0:y1, x0:x1]
        result[y0:y1, x0:x1] = region*(1-weight) + value*weight
    reference = float(settings.get("zero_reference", .5))
    point = settings.get('reference_point')
    if point is not None:
        if not isinstance(point,dict) or set(point) != {'x','y'} or not all(
                isinstance(v,(int,float)) and not isinstance(v,bool) and np.isfinite(v) and 0<=v<=1 for v in point.values()):
            raise ValueError('Referans noktası geçersiz.')
        # Sample full-precision edited depth, avoiding the browser's 8-bit preview drift.
        reference = float(result[round(point['y']*(height-1)),round(point['x']*(width-1))])
    effect = float(settings.get("effect_strength", 1))
    if not 0 <= reference <= 1 or not 0 <= effect <= 3:
        raise ValueError("Sabit derinlik 0–1, etki gücü 0–3 arasında olmalı.")
    before = result.copy()
    gain = effect*np.where(result>=reference, settings.get("front_strength",1), settings.get("back_strength",1))
    delta = result-reference
    linear = reference+delta*gain
    if settings.get("depth_curve","linear") == "soft":
        room = np.where(delta>=0,1-reference,reference)
        delta = delta*gain/(1+np.maximum(gain-1,0)*np.abs(delta)/np.maximum(room,1e-8))
        result = np.clip(reference+delta,0,1).astype(np.float32)
        clipped = 0.0
    else:
        clipped = float(np.mean((linear<0)|(linear>1)))
        result = np.clip(linear,0,1).astype(np.float32)
    return result, {"clipped_fraction":clipped, "linear_would_clip_fraction":float(np.mean((linear<0)|(linear>1))),
                    "depth_curve":settings.get("depth_curve","linear"),
                    "stroke_count":len(strokes), "zero_reference":reference,
                    "input_range":[float(before.min()),float(before.max())],
                    "output_range":[float(result.min()),float(result.max())]}


def plan_parallax(depth, size, settings):
    """Bound endpoint displacement in the motion axis; this is a geometric budget, not a comfort standard."""
    import math
    near, far = 1.5,3.0
    reference = settings["zero_reference"]
    zero = 1/((1-reference)/far+reference/near)
    requested = settings["angle_deg"]
    span = 2*zero*math.tan(math.radians(requested)/2)
    width,height = size
    extent = width if settings["camera_axis"] == "x" else height
    focal = width*50/36
    disparity = focal*span*(1/zero-((1-depth)/far+depth/near))
    requested_fraction = float(np.max(np.abs(disparity)))/extent
    # A robust local discontinuity heuristic, normalized to a 512-pixel working image.
    axis = 1 if settings["camera_axis"] == "x" else 0
    jumps = np.abs(np.diff(disparity,axis=axis))*.5*512/extent
    requested_edge = float(np.quantile(jumps,.995)) if jumps.size else 0
    limit = settings.get("max_parallax_percent",3)/100
    factor = min(1,limit/max(requested_fraction,1e-12)) if settings.get("parallax_guard",True) else 1
    edge_factor = min(1,1.5/max(requested_edge,1e-12)) if settings.get("edge_guard",True) else 1
    factor = min(factor,edge_factor)
    span *= factor
    disparity *= factor
    effective = math.degrees(2*math.atan(span/(2*zero)))
    stats = dict(requested_angle_deg=requested,effective_angle_deg=effective,
        angle_limited=factor<.999999,parallax_limit_percent=limit*100,
        endpoint_disparity_px_range=[float(disparity.min()),float(disparity.max())],
        max_parallax_percent=float(np.max(np.abs(disparity)))/extent*100,
        adjacent_view_step_px=float(np.max(np.abs(disparity)))/max(settings["nr"]-1,1),
        edge_limited=edge_factor<1,edge_jump_p995_px_at_512=requested_edge*factor,
        requested_edge_jump_p995_px_at_512=requested_edge,
        requested_parallax_percent=requested_fraction*100,
        note="Endpoint motion relative to the zero plane; a configurable geometric budget, not a measured optical limit.")
    return dict(near=near,far=far,zero=zero,camera_span=span),stats,disparity


def save_parallax_map(disparity, output):
    # Cyan = behind the print, coral = in front; black = fixed plane.
    limit = max(float(np.max(np.abs(disparity))),1e-8)
    colors = np.where((disparity>=0)[...,None],np.array([70,180,255]),np.array([255,110,85]))
    rgb = np.rint(colors*np.abs(disparity)[...,None]/limit).astype(np.uint8)
    Image.fromarray(rgb).save(output)


def background_layers(photo, depth, output, config, count=3, radius=5):
    """Original surface stays untouched. Only hidden layers get Telea estimates."""
    import cv2
    output = Path(output)
    rgb = np.asarray(photo.convert("RGB"))
    if type(count) is not int or not 1 <= count <= 8 or not 1 <= radius <= 20:
        raise ValueError("Arka plan katman/radius ayarı geçersiz.")
    thresholds = np.unique(np.quantile(depth, np.linspace(.12, .8, count)))
    width, height = photo.size
    focal = width * config["focal_mm"] / config["sensor_width_mm"]
    span = max(abs(x) for x in config["positions"])
    padding = max(4, int(np.ceil(focal*span*(1/config["near"]-1/config["far"])))+4)
    layers, details = [], []
    for index, threshold in enumerate(thresholds):
        # Expand around foreground silhouettes to avoid copying their edge colors behind them.
        mask = (depth > threshold).astype(np.uint8)*255
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8))
        if np.all(mask):
            continue
        color = cv2.inpaint(rgb, mask, radius, cv2.INPAINT_TELEA)
        # Telea's gradient correction operates in image-value units. Applying it
        # directly to 0..1 depth produced large artificial relief in hidden areas.
        inferred = cv2.inpaint(depth*255.0, mask, radius, cv2.INPAINT_TELEA)/255.0
        # Keep hidden layers slightly behind visible surfaces, avoiding coplanar flicker.
        inferred = (np.clip(inferred, 0, float(threshold))-.003).astype(np.float32)
        background_config = config | {"edge_threshold":1.0}
        mesh, stats = build_mesh(inferred, background_config, padding=padding)
        texture_name, mesh_name = f"background_{index:02d}.png", f"background_{index:02d}.npz"
        texture = Image.fromarray(color).convert("RGBA")
        if index:
            # Near repair layers may only show the area that was actually removed
            # and filled. The old opaque surface repeated intact people just behind
            # the real photo, creating displaced silhouette echoes in side views.
            texture.putalpha(Image.fromarray(mask))
        texture.save(output / texture_name)
        np.savez_compressed(output / mesh_name, **mesh)
        Image.fromarray(mask).save(output / f"background_mask_{index:02d}.png")
        layers.append({"mesh":mesh_name, "texture":texture_name, "name":f"Estimated background {index+1}", "extend":index==0})
        details.append({"threshold":float(threshold), "estimated_source_fraction":float(np.mean(mask > 0)),
                        "visibility":"base" if index==0 else "inpainted region only", "mesh":stats})
    report = {"engine":"OpenCV Telea layered background", "layers":details,
              "padding_px":padding, "note":"Hidden content is an estimate, not recovered original content. Foreground photo pixels are preserved."}
    (output / "repair.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return layers
