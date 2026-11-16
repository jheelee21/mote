from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mote.config import Settings
from mote.main import create_app

AUTH = {"Authorization": "Bearer t0ken"}


@pytest.fixture
def client(tmp_path: Path):
    app = create_app(Settings(token="t0ken", data_dir=tmp_path / "data"))
    with TestClient(app) as c:
        yield c


def test_health_is_public(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["embedder"] == "dummy"


def test_token_required(client):
    assert client.get("/libraries").status_code == 401
    assert client.get("/libraries", headers=AUTH).status_code == 200


def test_add_and_scan_library(client, photo_dir: Path):
    r = client.post("/libraries", json={"root_path": str(photo_dir)}, headers=AUTH)
    assert r.status_code == 201
    lib = r.json()

    r = client.post(f"/libraries/{lib['id']}/scan", headers=AUTH)
    assert r.status_code == 202
    job_id = r.json()["id"]

    import time

    for _ in range(50):
        job = client.get(f"/jobs/{job_id}", headers=AUTH).json()
        if job["status"] in ("done", "failed"):
            break
        time.sleep(0.05)
    assert job["status"] == "done", job

    libs = client.get("/libraries", headers=AUTH).json()
    assert libs[0]["photo_count"] == 4


def test_duplicate_library_rejected(client, photo_dir: Path):
    client.post("/libraries", json={"root_path": str(photo_dir)}, headers=AUTH)
    r = client.post("/libraries", json={"root_path": str(photo_dir)}, headers=AUTH)
    assert r.status_code == 409
