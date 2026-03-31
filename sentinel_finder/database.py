from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable


class IndexDatabase:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS indexed_roots (
                    path TEXT PRIMARY KEY
                );

                CREATE TABLE IF NOT EXISTS files (
                    path TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    extension TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    modified_ts REAL NOT NULL,
                    created_ts REAL NOT NULL,
                    content_text TEXT NOT NULL,
                    content_excerpt TEXT NOT NULL,
                    indexed_ts REAL NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_files_name ON files(name);
                CREATE INDEX IF NOT EXISTS idx_files_extension ON files(extension);
                CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type);
                CREATE INDEX IF NOT EXISTS idx_files_modified ON files(modified_ts);
                """
            )

    def replace_roots(self, roots: Iterable[str]) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM indexed_roots")
            conn.executemany(
                "INSERT INTO indexed_roots(path) VALUES (?)",
                [(root,) for root in roots],
            )

    def load_roots(self) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute("SELECT path FROM indexed_roots ORDER BY path").fetchall()
        return [row["path"] for row in rows]
