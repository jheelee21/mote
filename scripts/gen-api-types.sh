#!/usr/bin/env bash
# Regenerate packages/api-types/src/schema.ts from the backend's OpenAPI schema.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_JSON="$ROOT/packages/api-types/openapi.json"

(cd "$ROOT/backend" && uv run mote openapi > "$OUT_JSON")
pnpm --filter @mote/api-types exec openapi-typescript "$OUT_JSON" -o src/schema.ts
echo "Wrote packages/api-types/src/schema.ts"
