from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from sentinel_finder.config import AppPaths


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sentinel-config-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_docs_can_be_resolved_from_bundle_root(self) -> None:
        writable_root = self.temp_dir / "writable"
        bundle_root = self.temp_dir / "bundle"
        app_paths = AppPaths(writable_root, bundle_root=bundle_root)
        self.assertEqual(app_paths.data_dir, writable_root / "index_store")
        self.assertEqual(app_paths.log_dir, writable_root / "logs")
        self.assertEqual(app_paths.docs_path, bundle_root / "docs")


if __name__ == "__main__":
    unittest.main()
