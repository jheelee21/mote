"""Small, explicit query helpers. Keep SQL here, not in routers or jobs."""

from __future__ import annotations

from collections.abc import Iterable

from mote.db.database import Database
from mote.pipeline.scan import ScannedFile

# --- libraries ---------------------------------------------------------------

_LIBRARY_SELECT = """
    SELECT l.id, l.root_path, l.name, l.added_at, l.last_scan_at,
           (SELECT COUNT(*) FROM photos p
             WHERE p.library_id = l.id AND p.status != 'missing') AS photo_count
    FROM libraries l
"""


def list_libraries(db: Database) -> list[dict]:
    return db.query(_LIBRARY_SELECT + " ORDER BY l.added_at")


def get_library(db: Database, library_id: int) -> dict | None:
    return db.query_one(_LIBRARY_SELECT + " WHERE l.id = ?", (library_id,))


def get_library_by_path(db: Database, root_path: str) -> dict | None:
    return db.query_one(_LIBRARY_SELECT + " WHERE l.root_path = ?", (root_path,))


def create_library(db: Database, root_path: str, name: str) -> int:
    with db.tx() as c:
        cur = c.execute("INSERT INTO libraries (root_path, name) VALUES (?, ?)", (root_path, name))
        return int(cur.lastrowid)


def delete_library(db: Database, library_id: int) -> None:
    with db.tx() as c:
        c.execute("DELETE FROM libraries WHERE id = ?", (library_id,))


def mark_scanned(db: Database, library_id: int) -> None:
    with db.tx() as c:
        c.execute(
            "UPDATE libraries SET last_scan_at = datetime('now'), is_online = 1 WHERE id = ?",
            (library_id,),
        )


# --- photos ------------------------------------------------------------------


def known_files(db: Database, library_id: int) -> dict[str, tuple[int, float]]:
    """path -> (size, mtime) for every photo already recorded in a library."""
    rows = db.query("SELECT path, size, mtime FROM photos WHERE library_id = ?", (library_id,))
    return {r["path"]: (r["size"], r["mtime"]) for r in rows}


def upsert_photos(db: Database, library_id: int, files: Iterable[ScannedFile]) -> int:
    """Insert new files and reset changed ones to 'new' so they are re-indexed."""
    n = 0
    with db.tx() as c:
        for f in files:
            c.execute(
                """
                INSERT INTO photos (library_id, path, size, mtime, format, is_raw, status)
                VALUES (?, ?, ?, ?, ?, ?, 'new')
                ON CONFLICT(path) DO UPDATE SET
                    size = excluded.size, mtime = excluded.mtime,
                    status = 'new', error = NULL
                """,
                (library_id, f.path, f.size, f.mtime, f.format, int(f.is_raw)),
            )
            n += 1
    return n


def mark_missing(db: Database, paths: Iterable[str]) -> int:
    """Flag photos whose files disappeared. Rows are kept so user edits survive."""
    n = 0
    with db.tx() as c:
        for p in paths:
            c.execute("UPDATE photos SET status = 'missing' WHERE path = ?", (p,))
            n += 1
    return n
