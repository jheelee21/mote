"""Thumbnail generation. RAW files use their embedded JPEG preview (via rawpy)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

THUMB_SIZES = (256, 1024)


def load_image(path: Path, is_raw: bool = False) -> Image.Image:
    """Open a photo as an RGB PIL image, honouring EXIF orientation."""
    if is_raw:
        return _load_raw_preview(path)
    with Image.open(path) as im:
        im = ImageOps.exif_transpose(im)
        return im.convert("RGB")


def _load_raw_preview(path: Path) -> Image.Image:
    try:
        import io

        import rawpy
    except ImportError as exc:  # optional extra: `uv sync --extra raw`
        raise RuntimeError("RAW support needs the 'raw' extra (rawpy)") from exc
    with rawpy.imread(str(path)) as raw:
        thumb = raw.extract_thumb()
        if thumb.format == rawpy.ThumbFormat.JPEG:
            return Image.open(io.BytesIO(thumb.data)).convert("RGB")
        return Image.fromarray(thumb.data).convert("RGB")


def make_thumbnail(image: Image.Image, size: int) -> Image.Image:
    thumb = image.copy()
    thumb.thumbnail((size, size), Image.Resampling.LANCZOS)
    return thumb


def thumb_path(cache_dir: Path, photo_id: int, size: int) -> Path:
    """Shard by id so no folder holds more than ~1000 files."""
    return cache_dir / str(size) / f"{photo_id // 1000:04d}" / f"{photo_id}.webp"


def write_thumbnails(image: Image.Image, cache_dir: Path, photo_id: int) -> dict[int, Path]:
    out = {}
    for size in THUMB_SIZES:
        p = thumb_path(cache_dir, photo_id, size)
        p.parent.mkdir(parents=True, exist_ok=True)
        make_thumbnail(image, size).save(p, "WEBP", quality=82)
        out[size] = p
    return out
