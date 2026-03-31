from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from .config import AppPaths, resolve_runtime_roots
from .database import IndexDatabase
from .indexer import FileIndexer
from .search_engine import SearchEngine
from .ui import create_app_window


def configure_logging(app_paths: AppPaths) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(app_paths.log_path, encoding="utf-8"),
        ],
        force=True,
    )


def main() -> int:
    project_root, bundle_root = resolve_runtime_roots()
    app_paths = AppPaths(project_root, bundle_root=bundle_root)
    configure_logging(app_paths)
    app = QApplication(sys.argv)
    db = IndexDatabase(app_paths.db_path)
    indexer = FileIndexer(db, app_paths.model_path)
    search_engine = SearchEngine(db, app_paths.model_path)
    window = create_app_window(db, indexer, search_engine, app_paths)
    window.show()
    return app.exec()
