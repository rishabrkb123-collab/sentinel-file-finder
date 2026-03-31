from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import sentinel_finder.indexer as indexer_module
from sentinel_finder.config import AppPaths
from sentinel_finder.database import IndexDatabase
from sentinel_finder.indexer import FileIndexer
from sentinel_finder.models import SearchFilters
from sentinel_finder.search_engine import SearchEngine


class SearchEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = Path(tempfile.mkdtemp(prefix="sentinel-tests-"))
        self.root = self.temp_dir / "files"
        self.root.mkdir()
        (self.root / "alpha_sample.txt").write_text("project sample content", encoding="utf-8")
        (self.root / "sample_beta.txt").write_text("beta content", encoding="utf-8")
        (self.root / "alpha_sample_beta.pdf").write_bytes(b"%PDF-test")
        (self.root / "notes.md").write_text("semantic finder architecture", encoding="utf-8")

        self.app_paths = AppPaths(self.temp_dir)
        self.db = IndexDatabase(self.app_paths.db_path)
        self.indexer = FileIndexer(self.db, self.app_paths.model_path)
        self.search_engine = SearchEngine(self.db, self.app_paths.model_path)
        self.original_extract_text = indexer_module.extract_text
        indexer_module.extract_text = self._safe_extract_text
        self.indexer.rebuild_index([str(self.root)])

    def tearDown(self) -> None:
        indexer_module.extract_text = self.original_extract_text
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _safe_extract_text(self, file_path: Path) -> str:
        if file_path.suffix.lower() == ".pdf":
            return ""
        return self.original_extract_text(file_path)

    def test_wildcard_endswith_search(self) -> None:
        results = self.search_engine.search(SearchFilters(query="**sample", limit=10))
        self.assertEqual([item["name"] for item in results], ["alpha_sample.txt"])

    def test_wildcard_startswith_search(self) -> None:
        results = self.search_engine.search(SearchFilters(query="sample**", limit=10))
        self.assertEqual([item["name"] for item in results], ["sample_beta.txt"])

    def test_wildcard_contains_with_extension(self) -> None:
        results = self.search_engine.search(SearchFilters(query="**sample**.pdf", limit=10))
        self.assertEqual([item["name"] for item in results], ["alpha_sample_beta.pdf"])

    def test_semantic_search_returns_relevant_file(self) -> None:
        results = self.search_engine.search(SearchFilters(query="finder architecture", limit=5))
        self.assertEqual(results[0]["name"], "notes.md")


if __name__ == "__main__":
    unittest.main()
