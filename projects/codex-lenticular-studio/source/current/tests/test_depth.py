import tempfile
import hashlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np

from lenticular.depth import check_destination, estimate, model_file, proximity_from_depth


class DepthChecks(unittest.TestCase):
    def test_direct_depth_is_inverted(self):
        depth = np.linspace(1, 10, 1000, dtype=np.float32).reshape(20, 50)
        proximity, bounds = proximity_from_depth(depth)
        self.assertEqual(proximity.dtype, np.float32)
        self.assertEqual(proximity.shape, depth.shape)
        self.assertEqual(float(proximity[0, 0]), 1)
        self.assertEqual(float(proximity[-1, -1]), 0)
        self.assertTrue(np.all(np.diff(proximity.ravel()) <= 0))
        self.assertEqual(bounds["clipped_fraction"], 0.0)
        self.assertEqual(bounds["inverse_depth_percentiles"], [0, 100])

    def test_reject_bad_or_flat_depth(self):
        for values in (np.ones((4, 4)), [[0, 1]], [[-1, 1]],
                       [[float("nan"), 1]], [[float("inf"), 1]], [1, 2], np.empty((0, 2))):
            with self.subTest(values=str(values)), self.assertRaises(ValueError):
                proximity_from_depth(values)

    def test_sources_rejected_before_model_import_or_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "sources" / "depth"
            with self.assertRaises(ValueError):
                estimate("missing.png", target)
            with self.assertRaises(ValueError):
                check_destination(target)
            self.assertFalse(target.exists())

    def test_checked_cache_is_reused_and_corruption_rejected(self):
        data = b"verified model artifact"
        with tempfile.TemporaryDirectory() as folder, patch("lenticular.depth.ARTIFACTS",
                {"config.json": (len(data), hashlib.sha256(data).hexdigest())}):
            with patch("lenticular.depth.urllib.request.urlopen", return_value=io.BytesIO(data)) as fetch:
                path = model_file(folder, "config.json")
                self.assertEqual(path.read_bytes(), data)
                self.assertEqual(model_file(folder, "config.json"), path)
                self.assertEqual(fetch.call_count, 1)
                path.write_bytes(b"bad cache")
                with self.assertRaises(RuntimeError):
                    model_file(folder, "config.json")
                self.assertEqual(fetch.call_count, 1)


if __name__ == "__main__":
    unittest.main()
