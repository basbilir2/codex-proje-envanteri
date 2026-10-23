"""User-defined object depth edits; move a region without painting its relief flat."""
import math
import cv2
import numpy as np


def validate_regions(regions):
    if not isinstance(regions, list) or len(regions) > 32:
        raise ValueError('En fazla 32 nesne bölgesi kullanılabilir.')
    for region in regions:
        if not isinstance(region, dict) or set(region) != {'points', 'offset', 'relief'}:
            raise ValueError('Nesne bölgesi kaydı geçersiz.')
        points = region['points']
        if not isinstance(points, list) or not 3 <= len(points) <= 128:
            raise ValueError('Nesne sınırı 3–128 nokta içermeli.')
        for point in points:
            if not isinstance(point, list) or len(point) != 2 or any(
                isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in point):
                raise ValueError('Nesne sınırı fotoğrafın içinde olmalı.')
        for key, low, high in [('offset', -.5, .5), ('relief', 0, 3)]:
            v = region[key]
            if isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v) or not low <= v <= high:
                raise ValueError('Nesne konumu veya hacim ayarı geçersiz.')
        if abs(cv2.contourArea(np.asarray(points, np.float32))) < 1e-6:
            raise ValueError('Nesne sınırı bir alan çevrelemeli.')
    return regions


def region_mask(points, shape):
    h,w = shape
    contour = np.rint(np.asarray(points)*[w-1,h-1]).astype(np.int32)
    return cv2.fillPoly(np.zeros(shape,np.uint8), [contour], 1).astype(bool)


def edit_objects(depth, regions):
    validate_regions(regions)
    result = depth.copy()
    records = []
    for index, region in enumerate(regions):
        mask = region_mask(region['points'], result.shape)
        values = result[mask]
        pivot = float(np.median(values))
        center = float(np.clip(pivot+region['offset'],0,1))
        delta = values-pivot
        gain = region['relief']
        if delta.max() > 0: gain = min(gain, (1-center)/float(delta.max()))
        if delta.min() < 0: gain = min(gain, center/float(-delta.min()))
        # Scale the entire shape when space runs out; never clip only its peaks.
        result[mask] = center+gain*delta
        records.append(dict(index=index, fraction=float(mask.mean()), input_relief=float(np.ptp(values)),
            output_relief=float(np.ptp(result[mask])), requested_gain=region['relief'], applied_gain=gain,
            center=center, range_limited=gain < region['relief']-1e-6))
    return result, records
