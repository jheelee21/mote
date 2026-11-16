"""Find photo files under a folder and diff them against what is already indexed."""

from __future__ import annotations

import os
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

RASTER_EXTS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".heic", ".heif", ".webp"}
RAW_EXTS = {
    ".arw",
    ".cr2",
    ".cr3",
    ".nef",
    ".nrw",
    ".orf",
    ".raf",
    ".rw2",
    ".dng",
    ".pef",
    ".srw",
    ".3fr",
    ".iiq",
    ".x3f",
}
SUPPORTED_EXTS = RASTER_EXTS | RAW_EXTS


@dataclass(frozen=True)
class ScannedFile:
    path: str
    size: int
    mtime: float
    format: str
    is_raw: bool


def scan_folder(root: Path) -> Iterator[ScannedFile]:
    """Yield supported image files under `root`, skipping hidden files and folders."""
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in filenames:
            if name.startswith("."):
                continue
            ext = os.path.splitext(name)[1].lower()
            if ext not in SUPPORTED_EXTS:
                continue
            full = os.path.join(dirpath, name)
            try:
                st = os.stat(full)
            except OSError:
                continue
            yield ScannedFile(
                path=os.path.abspath(full),
                size=st.st_size,
                mtime=st.st_mtime,
                format=ext.lstrip("."),
                is_raw=ext in RAW_EXTS,
            )


def diff_scan(
    found: Iterable[ScannedFile], known: dict[str, tuple[int, float]]
) -> tuple[list[ScannedFile], list[str]]:
    """Return (new_or_changed, missing_paths) given the files on disk and the indexed ones."""
    changed: list[ScannedFile] = []
    seen: set[str] = set()
    for f in found:
        seen.add(f.path)
        prev = known.get(f.path)
        if prev is None or prev != (f.size, f.mtime):
            changed.append(f)
    missing = [p for p in known if p not in seen]
    return changed, missing
