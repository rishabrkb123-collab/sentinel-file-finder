from __future__ import annotations

import math
from dataclasses import asdict
from difflib import SequenceMatcher
from typing import Any

import joblib
from sklearn.metrics.pairwise import cosine_similarity

from .models import FileRecord, SearchFilters


class SearchEngine:
    def __init__(self, db, model_path) -> None:
        self.db = db
        self.model_path = model_path
        self._model_cache: dict[str, Any] | None = None

    def _load_model(self) -> dict[str, Any] | None:
        if self._model_cache is not None:
            return self._model_cache
        if not self.model_path.exists():
            return None
        self._model_cache = joblib.load(self.model_path)
        return self._model_cache

    def invalidate_model_cache(self) -> None:
        self._model_cache = None

    def search(self, filters: SearchFilters) -> list[dict[str, Any]]:
        sql = [
            """
            SELECT path, name, extension, file_type, size_bytes, modified_ts, created_ts, content_excerpt, content_text
            FROM files
            WHERE 1=1
            """
        ]
        params: list[Any] = []
        if filters.extension:
            sql.append("AND extension = ?")
            params.append(filters.extension.lower() if filters.extension.startswith(".") else f".{filters.extension.lower()}")
        if filters.file_type and filters.file_type != "Any":
            sql.append("AND file_type = ?")
            params.append(filters.file_type)
        if filters.path_contains:
            sql.append("AND path LIKE ?")
            params.append(f"%{filters.path_contains}%")
        if filters.min_size_mb is not None:
            sql.append("AND size_bytes >= ?")
            params.append(int(filters.min_size_mb * 1024 * 1024))
        if filters.max_size_mb is not None:
            sql.append("AND size_bytes <= ?")
            params.append(int(filters.max_size_mb * 1024 * 1024))
        if filters.modified_after is not None:
            sql.append("AND modified_ts >= ?")
            params.append(filters.modified_after.timestamp())
        if filters.modified_before is not None:
            sql.append("AND modified_ts <= ?")
            params.append(filters.modified_before.timestamp())
        if filters.content_only:
            sql.append("AND LENGTH(TRIM(content_text)) > 0")

        with self.db.connect() as conn:
            rows = conn.execute("\n".join(sql), params).fetchall()

        records = [
            FileRecord(
                path=row["path"],
                name=row["name"],
                extension=row["extension"],
                file_type=row["file_type"],
                size_bytes=row["size_bytes"],
                modified_ts=row["modified_ts"],
                created_ts=row["created_ts"],
                content_excerpt=row["content_excerpt"],
            )
            for row in rows
        ]
        raw_content = {row["path"]: row["content_text"] for row in rows}
        return self._score_results(records, raw_content, filters)[: filters.limit]

    def _score_results(
        self,
        records: list[FileRecord],
        raw_content: dict[str, str],
        filters: SearchFilters,
    ) -> list[dict[str, Any]]:
        query = filters.query.strip()
        model = self._load_model()
        semantic_scores: dict[str, float] = {}
        if query and model and model.get("matrix") is not None:
            vectorizer = model["vectorizer"]
            matrix = model["matrix"]
            doc_paths = model["doc_paths"]
            query_vector = vectorizer.transform([query])
            similarities = cosine_similarity(query_vector, matrix).flatten()
            semantic_scores = {
                doc_paths[index]: float(score)
                for index, score in enumerate(similarities)
            }

        scored: list[dict[str, Any]] = []
        tokens = [token.lower() for token in query.split() if token.strip()]
        for record in records:
            haystack = f"{record.name} {record.path} {raw_content.get(record.path, '')}".lower()
            lexical = 0.0
            if query:
                for token in tokens:
                    if token in haystack:
                        lexical += 1.0
                lexical = lexical / max(len(tokens), 1)
                fuzzy = SequenceMatcher(None, query.lower(), record.name.lower()).ratio()
                semantic = semantic_scores.get(record.path, 0.0)
                exact_boost = 1.0 if query.lower() in haystack else 0.0
                score = (semantic * 0.55) + (lexical * 0.2) + (fuzzy * 0.15) + (exact_boost * 0.1)
            else:
                score = 0.01 + min(math.log2(record.size_bytes + 1) / 100.0, 0.1)
            scored.append({**asdict(record), "score": round(score, 4)})

        scored.sort(key=lambda item: (item["score"], item["modified_ts"]), reverse=True)
        return scored
