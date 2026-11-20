# Research

Experiments that inform product decisions. Notebooks import the real `mote` package, so they run the same pipeline as the app.

## Setup

```bash
cd backend
uv sync --extra ml --extra raw --group research
uv run jupyter lab ../research/notebooks
```

- `ml`: PyTorch, transformers, open_clip, scikit-learn, UMAP
- `raw`: rawpy, for RAW files (uses their embedded JPEG preview)
- `research`: Jupyter, pandas, matplotlib, tqdm

Model weights download to the Hugging Face cache (`~/.cache/huggingface`) the first time a model is used.

## Notebooks

| Notebook | Question |
|---|---|
| `01_model_comparison.ipynb` | Which Hugging Face image-text model should Mote use? Compares speed, memory, license, text search, clustering quality, auto-names, and labelled metrics on a sample of your photos. |

Planned:

- `02_cluster_tuning.ipynb`: tune `min_cluster_size`, UMAP settings and `signal_weight` for the chosen model.
- `03_series_selection.ipynb`: pick cohesive 9–12 photo series from a Story.

Shared helpers (photo sampling, preview and embedding caches, plots, metrics) live in `notebooks/nbutils.py`.

## Trying a new model

Add `"hf:<owner>/<repo>"` to `CANDIDATES` in the configuration cell. Supported:

- anything `transformers.AutoModel` loads with `get_image_features` / `get_text_features` (CLIP, SigLIP, SigLIP 2, MetaCLIP, ...)
- any repo that ships an `open_clip_config.json` (LAION, DFN, ...)

The same id works in the app: `uv run mote serve --embedder hf:<owner>/<repo>`.

## Caches and results

- `research/.cache/`: previews, tone signals and embeddings of your photos. Git-ignored. Delete it to start fresh.
- `research/results/`: CSV scorecards (metrics only, no paths or photos). Fine to commit.

## Never commit photos

Keep your photos outside the repo. `eval/` stores only manifests (paths and labels) and metric scripts; keep a real `labels.csv` with private paths out of git.
