from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class AppPaths:
    project_root: Path
    bundle_root: Path | None = None
    data_dir: Path = field(init=False)
    db_path: Path = field(init=False)
    model_path: Path = field(init=False)
    docs_path: Path = field(init=False)
    log_dir: Path = field(init=False)
    log_path: Path = field(init=False)

    def __post_init__(self) -> None:
        bundle_root = self.bundle_root or self.project_root
        self.data_dir = self.project_root / "index_store"
        self.db_path = self.data_dir / "sentinel_index.sqlite3"
        self.model_path = self.data_dir / "search_model.joblib"
        self.docs_path = bundle_root / "docs"
        self.log_dir = self.project_root / "logs"
        self.log_path = self.log_dir / "sentinel.log"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


def resolve_runtime_roots() -> tuple[Path, Path]:
    if getattr(sys, "frozen", False):
        local_app_data = os.getenv("LOCALAPPDATA")
        writable_root = (
            Path(local_app_data) / "SentinelFileFinder"
            if local_app_data
            else Path(sys.executable).resolve().parent / "user_data"
        )
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        return writable_root, bundle_root
    root = Path(__file__).resolve().parent.parent
    return root, root


SUPPORTED_TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".rst",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".csv",
    ".log",
    ".xml",
    ".html",
    ".css",
    ".java",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".go",
    ".rs",
    ".sql",
}

MAX_CONTENT_BYTES = 5 * 1024 * 1024
SNIPPET_CHARS = 2000
