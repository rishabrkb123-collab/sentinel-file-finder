from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(slots=True)
class SearchFilters:
    query: str = ""
    extension: str = ""
    file_type: str = "Any"
    path_contains: str = ""
    min_size_mb: float | None = None
    max_size_mb: float | None = None
    modified_after: datetime | None = None
    modified_before: datetime | None = None
    content_only: bool = False
    limit: int = 200


@dataclass(slots=True)
class FileRecord:
    path: str
    name: str
    extension: str
    file_type: str
    size_bytes: int
    modified_ts: float
    created_ts: float
    content_excerpt: str

    @property
    def modified_dt(self) -> datetime:
        return datetime.fromtimestamp(self.modified_ts)

    @property
    def created_dt(self) -> datetime:
        return datetime.fromtimestamp(self.created_ts)

    @property
    def path_obj(self) -> Path:
        return Path(self.path)
