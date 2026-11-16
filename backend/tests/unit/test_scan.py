from pathlib import Path

from mote.pipeline.scan import diff_scan, scan_folder


def test_scan_finds_supported_files_and_skips_hidden(photo_dir: Path):
    names = sorted(Path(f.path).name for f in scan_folder(photo_dir))
    assert names == ["blue_hour.jpg", "fog.png", "golden.jpg", "raw_placeholder.NEF"]


def test_scan_flags_raw(photo_dir: Path):
    raw = {Path(f.path).name: f.is_raw for f in scan_folder(photo_dir)}
    assert raw["raw_placeholder.NEF"] is True
    assert raw["golden.jpg"] is False


def test_diff_scan_detects_new_changed_and_missing(photo_dir: Path):
    found = list(scan_folder(photo_dir))
    first = found[0]
    known = {
        first.path: (first.size, first.mtime),  # unchanged
        found[1].path: (found[1].size + 1, found[1].mtime),  # changed
        "/gone/old.jpg": (10, 1.0),  # missing
    }
    changed, missing = diff_scan(found, known)
    changed_paths = {f.path for f in changed}
    assert first.path not in changed_paths
    assert found[1].path in changed_paths
    assert missing == ["/gone/old.jpg"]
