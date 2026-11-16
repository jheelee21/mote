"""Job tasks: each takes a Job first, then keyword arguments."""

from __future__ import annotations

from pathlib import Path

from mote.db import repositories as repo
from mote.db.database import Database
from mote.jobs.queue import Job
from mote.pipeline.scan import diff_scan, scan_folder

BATCH = 500


def scan_library_task(job: Job, *, db: Database, library: dict) -> None:
    """Walk a library folder and record new, changed and missing photos."""
    root = Path(library["root_path"])
    job.update(message=f"Scanning {root}")

    found = []
    for i, f in enumerate(scan_folder(root), start=1):
        found.append(f)
        if i % BATCH == 0:
            job.update(progress=i, message=f"Found {i:,} photos")

    known = repo.known_files(db, library["id"])
    changed, missing = diff_scan(found, known)
    job.update(progress=0, total=len(changed), message="Recording changes")

    for start in range(0, len(changed), BATCH):
        repo.upsert_photos(db, library["id"], changed[start : start + BATCH])
        job.update(progress=min(start + BATCH, len(changed)))

    repo.mark_missing(db, missing)
    repo.mark_scanned(db, library["id"])
    job.update(
        message=(
            f"{len(found):,} photos · {len(changed):,} new or changed · {len(missing):,} missing"
        )
    )
