# Mote — notes for Claude

Mote is a local-first desktop app that discovers mood- and subject-based themes ("Stories") in a photographer's archive. Read `docs/architecture.md` before larger changes.

## Layout

- `apps/desktop/` — Tauri (Rust) + React/TypeScript UI. Rust stays thin: window, native dialogs, sidecar lifecycle.
- `backend/` — Python package `mote`: FastAPI sidecar, pipeline, models, DB, exports.
- `packages/api-types/` — TS types generated from the backend OpenAPI schema. Never hand-edit `src/schema.ts`.
- `research/` — notebooks and eval scripts. Never commit photos.

## Rules

- Never modify, move or delete a user's original photos. Exports copy or link; metadata goes to XMP sidecars only when enabled.
- Nothing leaves the user's machine: no network calls except optional model-weight downloads.
- `backend/src/mote/pipeline/` holds pure functions (no FastAPI, no DB imports). `jobs/` wires them to the DB and progress events.
- All embedding models implement `mote.models.base.Embedder`; never call a model library directly from pipeline code.
- API contract lives in pydantic schemas (`backend/src/mote/schemas/`). After changing them run `pnpm gen:api`.

## Commands

- Backend: `cd backend && uv sync && uv run mote serve --port 8765`
- Backend tests/lint: `cd backend && uv run pytest && uv run ruff check .`
- Desktop: `pnpm install && pnpm dev`
- Frontend tests/lint: `pnpm test && pnpm lint && pnpm typecheck`
