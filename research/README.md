# Research

Experiments that inform product decisions. Notebooks import the real `mote` package so they use the same pipeline as the app:

```bash
cd backend
uv sync --group research
uv run jupyter lab ../research/notebooks
```

## Planned notebooks

1. `01_spike_embed_cluster_name.ipynb` — embed ~2,000 photos, cluster (UMAP → HDBSCAN), auto-name clusters. Do the groups feel like real themes?
2. `02_model_comparison.ipynb` — compare candidate embedders on the eval set (quality, speed, memory, license).
3. `03_mood_vs_subject_weights.ipynb` — how much should color/light signals weigh against semantic embeddings?

## Never commit photos

Keep your photos outside the repo. `eval/` stores only manifests (paths + labels) and metric scripts.
