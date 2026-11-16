"""SQLite connection with simple, ordered SQL migrations.

Migrations live in `migrations/NNNN_name.sql` and are applied in order; the
applied version is tracked with `PRAGMA user_version`.
"""

from __future__ import annotations

import re
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).parent / "migrations"
_MIGRATION_RE = re.compile(r"^(\d{4})_.+\.sql$")


class Database:
    def __init__(self, path: Path | str):
        self.path = str(path)
        # One shared connection guarded by a lock: API handlers and job
        # threads both use it. WAL keeps reads cheap while a job writes.
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock:
            self._conn.execute("PRAGMA foreign_keys = ON")
            if self.path != ":memory:":
                self._conn.execute("PRAGMA journal_mode = WAL")

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        """Run statements in one transaction."""
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    def query(self, sql: str, params: tuple | dict = ()) -> list[dict]:
        with self._lock:
            return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def query_one(self, sql: str, params: tuple | dict = ()) -> dict | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    @property
    def version(self) -> int:
        with self._lock:
            return self._conn.execute("PRAGMA user_version").fetchone()[0]

    def migrate(self) -> int:
        """Apply pending migrations; returns the resulting schema version."""
        migrations = sorted(
            (int(m.group(1)), p)
            for p in MIGRATIONS_DIR.glob("*.sql")
            if (m := _MIGRATION_RE.match(p.name))
        )
        with self._lock:
            current = self.version
            for number, path in migrations:
                if number <= current:
                    continue
                self._conn.executescript(
                    f"BEGIN;\n{path.read_text()}\nPRAGMA user_version = {number};\nCOMMIT;"
                )
                current = number
        return current

    def close(self) -> None:
        with self._lock:
            self._conn.close()
