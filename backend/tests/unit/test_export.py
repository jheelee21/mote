from pathlib import Path

from mote.export.folder import export_to_folder


def test_copy_export_keeps_originals_and_dedupes_names(photo_dir: Path, tmp_path: Path):
    src = photo_dir / "2023" / "golden.jpg"
    out = tmp_path / "out"
    written = export_to_folder([src, src], out)
    assert [p.name for p in written] == ["golden.jpg", "golden-2.jpg"]
    assert src.exists()
