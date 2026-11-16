from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, status

from mote.api.deps import DbDep
from mote.db import repositories as repo
from mote.jobs.tasks import scan_library_task
from mote.schemas.jobs import JobOut
from mote.schemas.libraries import LibraryCreate, LibraryOut

router = APIRouter(prefix="/libraries", tags=["libraries"])


@router.get("", response_model=list[LibraryOut])
def list_libraries(db: DbDep) -> list[LibraryOut]:
    return [LibraryOut(**row) for row in repo.list_libraries(db)]


@router.post("", response_model=LibraryOut, status_code=status.HTTP_201_CREATED)
def add_library(body: LibraryCreate, db: DbDep) -> LibraryOut:
    root = Path(body.root_path).expanduser().resolve()
    if not root.is_dir():
        raise HTTPException(status_code=400, detail=f"not a directory: {root}")
    if repo.get_library_by_path(db, str(root)) is not None:
        raise HTTPException(status_code=409, detail="library already added")
    lib_id = repo.create_library(db, str(root), body.name or root.name)
    return LibraryOut(**repo.get_library(db, lib_id))


@router.delete("/{library_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_library(library_id: int, db: DbDep) -> None:
    """Forget a library. Never touches the photo files themselves."""
    if repo.get_library(db, library_id) is None:
        raise HTTPException(status_code=404, detail="library not found")
    repo.delete_library(db, library_id)


@router.post("/{library_id}/scan", response_model=JobOut, status_code=status.HTTP_202_ACCEPTED)
def scan_library(library_id: int, request: Request, db: DbDep) -> JobOut:
    lib = repo.get_library(db, library_id)
    if lib is None:
        raise HTTPException(status_code=404, detail="library not found")
    job = request.app.state.jobs.submit("scan", scan_library_task, db=db, library=lib)
    return JobOut(**job.as_dict())
