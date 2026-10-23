import tempfile
from pathlib import Path
import unittest

import numpy as np
from PIL import Image

from lenticular.geometry import build_mesh, read_depth, validate
from lenticular.cli import demo_inputs


class InputChecks(unittest.TestCase):
    def test_nr_ne_independent_and_explicit_path(self):
        config = validate({"nr":3, "ne":24, "positions":[-0.1, 0, 0.2]})
        self.assertEqual(config["nr"], 3)
        self.assertEqual(config["ne"], 24)
        self.assertEqual(config["positions"], [-0.1, 0, 0.2])

    def test_reject_undefined_or_invalid_projection(self):
        for config in ({"nr":1}, {"near":0}, {"far":1}, {"zero":0},
                       {"positions":[0, 1]}, {"edge_threshold":-1},
                       {"camera_span":float("nan")}, {"dpi":1200}, []):
            with self.subTest(config=config), self.assertRaises(ValueError):
                validate(config)

    def test_16bit_depth_preserved_and_direction_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "depth.png"
            Image.fromarray(np.array([[0, 21845, 65535]], dtype=np.uint16)).save(path)
            result = read_depth(path, (3, 1), "white-near")
            np.testing.assert_allclose(result, [[0, 1/3, 1]])
            np.testing.assert_allclose(read_depth(path, (3, 1), "black-near"), 1-result)
            with self.assertRaises(ValueError):
                read_depth(path, (4, 1), "white-near")

    def test_no_bridge_over_depth_boundary(self):
        depth = np.array([[0, 0, 1, 1]] * 4, dtype=np.float32)
        mesh, stats = build_mesh(depth, validate({"grid_size":4}))
        self.assertGreater(stats["cut_triangles"], 0)
        z = -mesh["vertices"][:, 2]
        spans = np.ptp(z[mesh["triangles"]], axis=1)
        self.assertEqual(float(spans.max()), 0)

    def test_demo_cannot_write_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "sources" / "demo"
            with self.assertRaises(ValueError):
                demo_inputs(target)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
