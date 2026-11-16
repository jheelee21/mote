from __future__ import annotations

from pydantic import BaseModel


class LibraryCreate(BaseModel):
    root_path: str
    name: str | None = None


class LibraryOut(BaseModel):
    id: int
    root_path: str
    name: str
    added_at: str
    last_scan_at: str | None
    photo_count: int = 0
