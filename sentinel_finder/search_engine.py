from __future__ import annotations

import math
import re
from dataclasses import asdict
from difflib import SequenceMatcher
from typing import Any

import joblib
from sklearn.metrics.pairwise import cosine_similarity

from .models import FileRecord, NamePattern, SearchFilters


WILDCARD_EXTENSION_RE = re.compile(r"^(?P<pattern>.+?)(?P<extension>\.[a-z0-9]{1,10})$", re.IGNORECASE)


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
        parsed_filters = self._prepare_filters(filters)
        sql = [
            """
            SELECT path, name, extension, file_type, size_bytes, modified_ts, created_ts, content_excerpt, content_text
            FROM files
            WHERE 1=1
            """
        ]
        params: list[Any] = []
        if parsed_filters.extension:
            sql.append("AND extension = ?")
            params.append(
                parsed_filters.extension.lower()
                if parsed_filters.extension.startswith(".")
                else f".{parsed_filters.extension.lower()}"
            )
        if parsed_filters.file_type and parsed_filters.file_type != "Any":
            sql.append("AND file_type = ?")
            params.append(parsed_filters.file_type)
        if parsed_filters.path_contains:
            sql.append("AND path LIKE ?")
            params.append(f"%{parsed_filters.path_contains}%")
        if parsed_filters.min_size_mb is not None:
            sql.append("AND size_bytes >= ?")
            params.append(int(parsed_filters.min_size_mb * 1024 * 1024))
        if parsed_filters.max_size_mb is not None:
            sql.append("AND size_bytes <= ?")
            params.append(int(parsed_filters.max_size_mb * 1024 * 1024))
        if parsed_filters.modified_after is not None:
            sql.append("AND modified_ts >= ?")
            params.append(parsed_filters.modified_after.timestamp())
        if parsed_filters.modified_before is not None:
            sql.append("AND modified_ts <= ?")
            params.append(parsed_filters.modified_before.timestamp())
        if parsed_filters.content_only:
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
        if parsed_filters.name_pattern:
            records = [record for record in records if self._matches_name_pattern(record, parsed_filters.name_pattern)]
            allowed_paths = {record.path for record in records}
            rows = [row for row in rows if row["path"] in allowed_paths]
        raw_content = {row["path"]: row["content_text"] for row in rows}
        return self._score_results(records, raw_content, parsed_filters)[: parsed_filters.limit]

    def _prepare_filters(self, filters: SearchFilters) -> SearchFilters:
        parsed_filters = SearchFilters(
            query=filters.query,
            extension=filters.extension,
            file_type=filters.file_type,
            path_contains=filters.path_contains,
            min_size_mb=filters.min_size_mb,
            max_size_mb=filters.max_size_mb,
            modified_after=filters.modified_after,
            modified_before=filters.modified_before,
            content_only=filters.content_only,
            limit=filters.limit,
            name_pattern=filters.name_pattern,
        )
        parsed_filters.query = filters.query.strip()
        pattern = self._parse_name_pattern(parsed_filters.query)
        if pattern:
            parsed_filters.name_pattern = pattern
            parsed_filters.query = pattern.text
            if not parsed_filters.extension and pattern.raw:
                extension_match = WILDCARD_EXTENSION_RE.match(pattern.raw)
                if extension_match:
                    parsed_filters.extension = extension_match.group("extension")
        return parsed_filters

    def _parse_name_pattern(self, query: str) -> NamePattern | None:
        candidate = query.strip()
        if "**" not in candidate:
            return None

        extension = ""
        extension_match = WILDCARD_EXTENSION_RE.match(candidate)
        if extension_match and "**" in extension_match.group("pattern"):
            candidate = extension_match.group("pattern")
            extension = extension_match.group("extension")

        mode = ""
        text = candidate
        if candidate.startswith("**") and candidate.endswith("**") and len(candidate) > 4:
            mode = "contains"
            text = candidate[2:-2]
        elif candidate.startswith("**") and len(candidate) > 2:
            mode = "endswith"
            text = candidate[2:]
        elif candidate.endswith("**") and len(candidate) > 2:
            mode = "startswith"
            text = candidate[:-2]

        text = text.strip()
        if not mode or not text:
            return None
        return NamePattern(text=text.lower(), mode=mode, raw=f"{candidate}{extension}".lower())

    def _matches_name_pattern(self, record: FileRecord, pattern: NamePattern) -> bool:
        filename = record.name.lower()
        stem = filename[: -len(record.extension)] if record.extension and filename.endswith(record.extension) else filename
        value = stem.lower()
        if pattern.mode == "startswith":
            return value.startswith(pattern.text)
        if pattern.mode == "endswith":
            return value.endswith(pattern.text)
        if pattern.mode == "contains":
            return pattern.text in value
        return False

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
                if filters.name_pattern and self._matches_name_pattern(record, filters.name_pattern):
                    score += 0.35
            else:
                score = 0.01 + min(math.log2(record.size_bytes + 1) / 100.0, 0.1)
            scored.append({**asdict(record), "score": round(score, 4)})

        scored.sort(key=lambda item: (item["score"], item["modified_ts"]), reverse=True)
        return scored
