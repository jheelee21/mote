from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from mote.db.database import Database


def _solid(path: Path, color: tuple[int, int, int], size=(64, 48)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)
    return path


@pytest.fixture
def photo_dir(tmp_path: Path) -> Path:
    """A tiny fake archive generated on the fly (no binary fixtures in git)."""
    root = tmp_path / "archive"
    _solid(root / "2023" / "blue_hour.jpg", (30, 45, 90))
    _solid(root / "2023" / "golden.jpg", (220, 160, 70))
    _solid(root / "2024" / "trip" / "fog.png", (180, 185, 180))
    (root / "2024" / "notes.txt").write_text("not a photo")
    _solid(root / ".hidden" / "skip.jpg", (0, 0, 0))
    (root / "2024" / "raw_placeholder.NEF").write_bytes(b"\x00" * 16)
    return root


@pytest.fixture
def db() -> Database:
    database = Database(":memory:")
    database.migrate()
    yield database
    database.close()
