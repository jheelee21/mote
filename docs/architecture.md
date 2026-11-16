# Architecture

## Overview

```
┌──────────────── Tauri app ────────────────┐
│  React UI  ──HTTP/JSON + SSE────────────┐ │
│  Rust core: dialogs, paths, sidecar mgmt│ │
└─────────────────────────────────────────┼─┘
                                          ▼
                  Python sidecar (FastAPI on 127.0.0.1)
                  ├─ api/        HTTP routers
                  ├─ jobs/       background queue + progress events
                  ├─ pipeline/   scan → thumbs → exif → embed → signals → cluster → name
                  ├─ models/     pluggable Embedder implementations
                  ├─ db/         SQLite schema + repositories
                  └─ export/     folder, XMP, contact sheet
```

## Sidecar lifecycle

1. On launch, Tauri picks a free port and a random token, then starts the `mote` sidecar with `serve --port <p> --token <t> --data-dir <app data dir>`.
2. Tauri polls `GET /health` until it answers, then passes `{port, token}` to the UI.
3. The UI sends `Authorization: Bearer <token>` on every request.
4. Tauri restarts the sidecar if it exits unexpectedly and kills it on quit.

In development you can run the backend on its own (`uv run mote serve --port 8765 --token dev`) and the UI picks it up from `VITE_MOTE_API`.

## Data flow

1. **Scan** library folders → `photos` rows (new / changed / missing).
2. **Thumbnails** into the on-disk cache (RAW → embedded JPEG preview).
3. **EXIF** → capture time, camera, lens, GPS.
4. **Embed** with the active `Embedder` → `embeddings` (one row per photo × model).
5. **Signals** → palette, warmth, saturation, brightness, time of day, season, people count, sharpness.
6. **Cluster** (UMAP → HDBSCAN on embedding + weighted signals) → `stories` + `story_photos`.
7. **Name** each cluster by zero-shot scoring against a theme vocabulary.

User edits (`story_photos.membership = added|removed`, pinned Stories, feedback) survive re-clustering.

## Storage

SQLite in the app data directory, plus a thumbnail cache folder. Embeddings are float32 BLOBs, loaded into an in-memory matrix for search. A dedicated vector index (sqlite-vec / FAISS) is deferred until needed.

## API contract

Pydantic schemas → FastAPI OpenAPI → `scripts/gen-api-types.sh` → `packages/api-types/src/schema.ts`. The frontend imports types from `@mote/api-types` only.

## Decisions

See `docs/decisions/`.
