"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mote import __version__
from mote.api import health, jobs, libraries
from mote.api.deps import require_token
from mote.config import Settings
from mote.db.database import Database
from mote.jobs.queue import JobQueue
from mote.models.registry import get_embedder

# Origins used by the Tauri webview and the Vite dev server.
ALLOWED_ORIGINS = [
    "tauri://localhost",
    "http://tauri.localhost",
    "https://tauri.localhost",
    "http://localhost:1420",
    "http://127.0.0.1:1420",
]


def create_app(settings: Settings, *, init_storage: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if init_storage:
            settings.ensure_dirs()
            app.state.db = Database(settings.db_path)
            app.state.db.migrate()
        app.state.jobs = JobQueue()
        try:
            yield
        finally:
            app.state.jobs.shutdown()
            if init_storage:
                app.state.db.close()

    app = FastAPI(title="Mote", version=__version__, lifespan=lifespan)
    app.state.settings = settings
    app.state.embedder = get_embedder(settings.embedder)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # /health stays unauthenticated so Tauri can poll it during startup.
    app.include_router(health.router)
    protected = [Depends(require_token)]
    app.include_router(libraries.router, dependencies=protected)
    app.include_router(jobs.router, dependencies=protected)
    return app
