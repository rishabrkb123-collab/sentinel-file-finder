from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class AppPaths:
    project_root: Path
    data_dir: Path = field(init=False)
    db_path: Path = field(init=False)
    model_path: Path = field(init=False)
    docs_path: Path = field(init=False)

    def __post_init__(self) -> None:
        self.data_dir = self.project_root / "index_store"
        self.db_path = self.data_dir / "sentinel_index.sqlite3"
        self.model_path = self.data_dir / "search_model.joblib"
        self.docs_path = self.project_root / "docs"
        self.data_dir.mkdir(parents=True, exist_ok=True)


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

