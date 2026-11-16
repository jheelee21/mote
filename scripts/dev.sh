#!/usr/bin/env bash
# Start the backend sidecar and the desktop app together for development.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${MOTE_PORT:-8765}"
TOKEN="${MOTE_TOKEN:-dev}"

# Tauri refuses to compile if the sidecar binary listed in externalBin is
# missing. In dev we run the backend from source, so an empty placeholder is enough.
TRIPLE="$(rustc -vV | sed -n 's/^host: //p')"
EXT=""
case "$TRIPLE" in *windows*) EXT=".exe" ;; esac
BIN_DIR="$ROOT/apps/desktop/src-tauri/binaries"
mkdir -p "$BIN_DIR"
[ -e "$BIN_DIR/mote-sidecar-$TRIPLE$EXT" ] || touch "$BIN_DIR/mote-sidecar-$TRIPLE$EXT"

(
  cd "$ROOT/backend"
  uv run mote serve --port "$PORT" --token "$TOKEN" --data-dir "$ROOT/.mote-data"
) &
BACKEND_PID=$!
trap 'kill $BACKEND_PID 2>/dev/null || true' EXIT

cd "$ROOT"
# MOTE_API_* tells the Rust shell not to spawn a sidecar; VITE_* tells the UI where to connect.
MOTE_API_URL="http://127.0.0.1:$PORT" MOTE_API_TOKEN="$TOKEN" \
VITE_MOTE_API="http://127.0.0.1:$PORT" VITE_MOTE_TOKEN="$TOKEN" \
  pnpm dev
