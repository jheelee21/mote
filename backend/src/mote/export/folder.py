"""Export photos to a folder by copying or linking. Originals are never moved."""

from __future__ import annotations

import os
import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import Literal

Mode = Literal["copy", "link"]


def _unique(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    n = 2
    while (candidate := dest.with_name(f"{stem}-{n}{suffix}")).exists():
        n += 1
    return candidate


def export_to_folder(
    paths: Iterable[str | Path], dest_dir: Path, mode: Mode = "copy"
) -> list[Path]:
    """Copy (or symlink) each photo into `dest_dir`; name clashes get a -2, -3… suffix."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for src in map(Path, paths):
        if not src.is_file():
            continue
        target = _unique(dest_dir / src.name)
        if mode == "link":
            os.symlink(src.resolve(), target)
        else:
            shutil.copy2(src, target)
        written.append(target)
    return written
