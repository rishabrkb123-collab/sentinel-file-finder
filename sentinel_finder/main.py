from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .config import AppPaths
from .database import IndexDatabase
from .indexer import FileIndexer
from .search_engine import SearchEngine
from .ui import create_app_window


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    app_paths = AppPaths(project_root)
    app = QApplication(sys.argv)
    db = IndexDatabase(app_paths.db_path)
    indexer = FileIndexer(db, app_paths.model_path)
    search_engine = SearchEngine(db, app_paths.model_path)
    window = create_app_window(db, indexer, search_engine, app_paths)
    window.show()
    return app.exec()
