"""EXIF extraction: capture time, camera, lens, exposure and GPS."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExifData:
    taken_at: str | None = None
    camera: str | None = None
    lens: str | None = None
    focal_length: float | None = None
    iso: int | None = None
    aperture: float | None = None
    shutter: str | None = None
    gps_lat: float | None = None
    gps_lon: float | None = None


def read_exif(path: Path) -> ExifData:
    """TODO: implement with Pillow's getexif() for rasters and exiftool/rawpy for RAWs."""
    raise NotImplementedError
