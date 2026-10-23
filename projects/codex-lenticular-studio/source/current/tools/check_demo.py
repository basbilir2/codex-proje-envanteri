"""Validate actual rendered marker positions against the known synthetic scene."""
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image


def check(folder):
    folder = Path(folder)
    job = json.loads((folder / "job.json").read_text(encoding="utf-8"))
    records = json.loads((folder / "render_result.json").read_text(encoding="utf-8"))
    if len(records) != job["config"]["nr"]:
        raise AssertionError("Nr/frame count differs")
    measurements = []
    for record in records:
        with Image.open(folder / record["file"]) as image:
            pixels = np.asarray(image.convert("RGBA"))
        row = pixels[100]
        centers = []
        for source_x in (80, 240, 400):
            x = np.arange(source_x-20, source_x+21)
            white = x[np.all(row[x, :3] > 235, axis=1) & (row[x, 3] > 250)]
            if not len(white):
                raise AssertionError("Missing rendered marker")
            centers.append(float(white.mean()))
        measurements.append(centers)
    first, last = np.asarray(measurements[0]), np.asarray(measurements[-1])
    displacement = last-first
    fpx = job["mesh"]["focal_px"]
    span = records[-1]["camera_x"]-records[0]["camera_x"]
    expected = fpx*span*(1/2-np.array([1/3, 1/2, 1/1.5]))
    np.testing.assert_allclose(displacement, expected, atol=0.75)
    if np.ptp(np.asarray(measurements)[:, 1]) > 0.5:
        raise AssertionError("Zero-plane marker drifts")
    with Image.open(folder / "center.png") as image:
        center = np.asarray(image.convert("RGBA"))
    with Image.open(folder / "source.png") as image:
        source = np.asarray(image.convert("RGBA"))
    valid = center[:, :, 3] == 255
    error = np.mean(np.abs(center[:, :, :3].astype(float)-source[:, :, :3])[valid])
    if error > 1.5:
        raise AssertionError(f"Center source color/registration error: {error}")
    with Image.open(folder / "look-around.png") as image:
        assert image.n_frames == 2*job["config"]["nr"]-2
    result = dict(status="passed", nr=job["config"]["nr"], ne=job["config"]["ne"],
                  endpoint_marker_displacement_px=displacement.tolist(),
                  expected_displacement_px=expected.tolist(),
                  zero_marker_drift_px=float(np.ptp(np.asarray(measurements)[:, 1])),
                  center_mean_absolute_rgb_error=float(error))
    (folder / "verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    check(sys.argv[1])
