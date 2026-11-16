# Mote

**Your archive already has stories. Mote finds them.**

Mote is a local-first desktop app for photographers with large, unorganized photo archives. It analyzes your photos on your own computer, discovers themes by subject, tone and mood ("Blue-hour city", "Summer nature, golden light"), and turns them into **Stories** you can refine, build into series, and export.

> The curator, not the catalog. Mote sits on top of your existing folders and Lightroom setup. It never modifies your originals, and nothing leaves your machine.

## Status

Early development. Not usable yet.

## Planned features

- Automatic theme discovery across your whole archive
- Natural-language search ("lone figure under a streetlight")
- Refine Stories with "more like this / less like this"
- Best-of-burst and near-duplicate detection
- Series builder for portfolios, zines and grids
- Export to folders, Lightroom/Capture One keywords (XMP) and PDF contact sheets

## Tech stack

- **Desktop shell:** Tauri (Rust)
- **UI:** React + TypeScript (Vite)
- **Backend:** Python sidecar with FastAPI
- **ML:** PyTorch (embedding model to be chosen)
- **Storage:** SQLite

## Repository layout

```
apps/desktop/      Tauri + React desktop app
backend/           Python package `mote` (FastAPI sidecar, pipeline, models)
packages/api-types TypeScript types generated from the backend's OpenAPI schema
research/          Notebooks and evaluation scripts
scripts/           Dev, build and codegen helpers
docs/              Architecture notes and decision records
```

See [docs/architecture.md](docs/architecture.md) for details.
