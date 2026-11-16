from __future__ import annotations

from fastapi import APIRouter, Request

from mote import __version__
from mote.schemas.health import Health

router = APIRouter(tags=["health"])


@router.get("/health", response_model=Health)
def health(request: Request) -> Health:
    embedder = getattr(request.app.state, "embedder", None)
    return Health(status="ok", version=__version__, embedder=embedder.id if embedder else None)
