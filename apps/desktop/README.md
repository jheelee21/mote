# @mote/desktop

Tauri 2 + React desktop app. Rust is kept thin: it opens the window, starts and supervises the Python sidecar, and exposes native dialogs. All app logic lives in the backend.

## Develop

Run the backend yourself and point the app at it (fastest loop):

```bash
# terminal 1
cd backend && uv run mote serve --port 8765 --token dev

# terminal 2 (repo root)
MOTE_API_URL=http://127.0.0.1:8765 MOTE_API_TOKEN=dev pnpm dev
```

Or run `scripts/dev.sh`, which does both.

UI only, in a browser: `VITE_MOTE_API=http://127.0.0.1:8765 pnpm --filter @mote/desktop dev`, then open http://localhost:1420 (native dialogs won't work there).

## Build

```bash
cd backend && uv run python ../scripts/build_sidecar.py   # → src-tauri/binaries/mote-sidecar-<target>
cd .. && pnpm build
```

## Icons

`src-tauri/icons/` holds placeholders. Regenerate the full set (including `.icns` for macOS bundles) from a 1024px source with `pnpm --filter @mote/desktop tauri icon path/to/icon.png`.
