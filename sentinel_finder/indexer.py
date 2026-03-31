from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

from .database import IndexDatabase
from .text_extractors import extract_text


FILE_TYPE_MAP = {
    ".txt": "Document",
    ".md": "Document",
    ".pdf": "Document",
    ".docx": "Document",
    ".xlsx": "Spreadsheet",
    ".csv": "Spreadsheet",
    ".py": "Code",
    ".js": "Code",
    ".ts": "Code",
    ".tsx": "Code",
    ".jsx": "Code",
    ".java": "Code",
    ".c": "Code",
    ".cpp": "Code",
    ".go": "Code",
    ".rs": "Code",
    ".json": "Data",
    ".xml": "Data",
    ".yaml": "Data",
    ".yml": "Data",
    ".mp3": "Audio",
    ".wav": "Audio",
    ".mp4": "Video",
    ".mkv": "Video",
    ".jpg": "Image",
    ".jpeg": "Image",
    ".png": "Image",
}


def classify_file_type(file_path: Path) -> str:
    return FILE_TYPE_MAP.get(file_path.suffix.lower(), "Other")


class FileIndexer:
    def __init__(self, database: IndexDatabase, model_path: Path) -> None:
        self.database = database
        self.model_path = model_path

    def rebuild_index(
        self,
        roots: list[str],
        progress: Callable[[str], None] | None = None,
    ) -> tuple[int, int]:
        scanned = 0
        indexed_rows: list[tuple] = []
        documents: list[str] = []
        doc_paths: list[str] = []
        now = time.time()

        for root in roots:
            root_path = Path(root)
            if not root_path.exists():
                continue
            for file_path in root_path.rglob("*"):
                if not file_path.is_file():
                    continue
                scanned += 1
                if progress and scanned % 50 == 0:
                    progress(f"Scanning {scanned} files... latest: {file_path}")
                try:
                    stat = file_path.stat()
                except OSError:
                    continue

                content = extract_text(file_path)
                excerpt = content[:200]
                indexed_rows.append(
                    (
                        str(file_path),
                        file_path.name,
                        file_path.suffix.lower(),
                        classify_file_type(file_path),
                        stat.st_size,
                        stat.st_mtime,
                        stat.st_ctime,
                        content,
                        excerpt,
                        now,
                    )
                )
                documents.append(f"{file_path.name}\n{file_path.parent}\n{content}")
                doc_paths.append(str(file_path))

        temp_model_path = self.model_path.with_suffix(".joblib.tmp")
        try:
            self._train_model(documents, doc_paths, temp_model_path)
            self.database.replace_files_and_roots(indexed_rows, roots)
            os.replace(temp_model_path, self.model_path)
        finally:
            if temp_model_path.exists():
                temp_model_path.unlink()
        return scanned, len(indexed_rows)

    def _train_model(self, documents: list[str], doc_paths: list[str], target_path: Path) -> None:
        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            max_features=30000,
        )
        matrix = vectorizer.fit_transform(documents) if documents else None
        joblib.dump(
            {
                "vectorizer": vectorizer,
                "matrix": matrix,
                "doc_paths": doc_paths,
            },
            target_path,
        )
