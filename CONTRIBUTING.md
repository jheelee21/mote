# Contributing

Mote is in early development. Issues and ideas are welcome.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python 3.11+)
- Node.js 20+ and [pnpm](https://pnpm.io/)
- Rust toolchain and the [Tauri prerequisites](https://tauri.app/start/prerequisites/) for your OS

## Getting started

```bash
# backend
cd backend
uv sync
uv run mote serve --port 8765 --token dev

# desktop (in another terminal, from the repo root)
pnpm install
pnpm dev
```

`scripts/dev.sh` starts both.

## Before opening a PR

```bash
cd backend && uv run ruff check . && uv run pytest
cd .. && pnpm lint && pnpm typecheck && pnpm test
```

If you changed API schemas, run `pnpm gen:api` and commit the regenerated types.

## Ground rules

- Never commit photos, thumbnails, embeddings or databases.
- Never write to a user's original files except XMP sidecars when the user enabled it.
