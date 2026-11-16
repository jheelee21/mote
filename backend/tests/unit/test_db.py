from mote.db import repositories as repo
from mote.pipeline.scan import ScannedFile


def test_migrate_is_idempotent(db):
    v = db.version
    assert v >= 1
    assert db.migrate() == v


def test_library_crud_and_photo_upsert(db):
    lib_id = repo.create_library(db, "/photos", "Archive")
    f = ScannedFile(path="/photos/a.jpg", size=10, mtime=1.0, format="jpg", is_raw=False)
    repo.upsert_photos(db, lib_id, [f])
    repo.upsert_photos(db, lib_id, [f])  # upsert, not duplicate
    assert repo.get_library(db, lib_id)["photo_count"] == 1

    repo.mark_missing(db, ["/photos/a.jpg"])
    assert repo.get_library(db, lib_id)["photo_count"] == 0

    repo.delete_library(db, lib_id)
    assert repo.list_libraries(db) == []
