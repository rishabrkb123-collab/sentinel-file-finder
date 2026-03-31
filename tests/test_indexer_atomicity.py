from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from sentinel_finder.config import AppPaths
from sentinel_finder.database import IndexDatabase
from sentinel_finder.indexer import FileIndexer


class IndexerAtomicityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sentinel-atomicity-"))
        self.first_root = self.temp_dir / "first"
        self.second_root = self.temp_dir / "second"
        self.first_root.mkdir()
        self.second_root.mkdir()
        (self.first_root / "one.txt").write_text("first corpus", encoding="utf-8")
        (self.second_root / "two.txt").write_text("second corpus", encoding="utf-8")

        self.app_paths = AppPaths(self.temp_dir)
        self.db = IndexDatabase(self.app_paths.db_path)
        self.indexer = FileIndexer(self.db, self.app_paths.model_path)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_db_and_roots_remain_unchanged_when_model_write_fails(self) -> None:
        self.indexer.rebuild_index([str(self.first_root)])
        original_model_bytes = self.app_paths.model_path.read_bytes()

        original_train = self.indexer._train_model

        def failing_train(documents, doc_paths, target_path):
            raise RuntimeError("forced failure")

        self.indexer._train_model = failing_train
        try:
            with self.assertRaises(RuntimeError):
                self.indexer.rebuild_index([str(self.second_root)])
        finally:
            self.indexer._train_model = original_train

        with self.db.connect() as conn:
            paths = [row["path"] for row in conn.execute("SELECT path FROM files ORDER BY path")]
            roots = [row["path"] for row in conn.execute("SELECT path FROM indexed_roots ORDER BY path")]

        self.assertEqual(paths, [str(self.first_root / "one.txt")])
        self.assertEqual(roots, [str(self.first_root)])
        self.assertEqual(self.app_paths.model_path.read_bytes(), original_model_bytes)


if __name__ == "__main__":
    unittest.main()
