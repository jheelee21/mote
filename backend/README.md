# mote (backend)

Python sidecar for the Mote desktop app: FastAPI server, indexing pipeline, embedding models, SQLite storage and exports.

```bash
uv sync                      # core + dev tools
uv sync --extra ml           # add PyTorch, UMAP, HDBSCAN
uv run mote serve --port 8765 --token dev --data-dir ../.mote-data
uv run mote openapi          # print the OpenAPI schema (used by `pnpm gen:api`)
uv run pytest
```

## Layout

```
src/mote/
  cli.py        entry point: `mote serve`, `mote openapi`
  main.py       FastAPI app factory
  config.py     runtime settings (port, token, data dir)
  api/          routers + auth dependency
  schemas/      pydantic models = the API contract
  db/           SQLite connection, versioned SQL migrations, repositories
  jobs/         background job queue + progress events
  pipeline/     pure functions: scan, exif, thumbs, embed, signals, cluster, naming
  models/       Embedder interface + implementations + registry
  export/       folder, XMP, contact sheet
```

`pipeline/` must not import FastAPI or the database; `jobs/` connects them.
