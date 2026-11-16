# 0002 — Tech stack

- **Status:** accepted
- **Date:** 2026-11-16

## Decision

| Layer | Choice |
|---|---|
| Desktop shell | Tauri 2 (Rust) |
| UI | React + TypeScript, Vite |
| Backend | Python 3.11+ sidecar, FastAPI |
| ML | PyTorch; embedding model chosen later behind the `Embedder` interface |
| Storage | SQLite |

## Open

- Embedding model and whether weights ship with the app or download on first run.
- Vector storage beyond an in-memory matrix.
- Sidecar packaging (PyInstaller vs. Nuitka) and GPU support per platform.
- License.
