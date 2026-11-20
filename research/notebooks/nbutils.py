"""Helpers for the research notebooks.

Kept out of the `mote` package on purpose: this is experiment plumbing
(caching, plotting, metrics), not app code. Notebooks import it from this folder.
"""

from __future__ import annotations

import gc
import hashlib
import json
import random
import time
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from mote.models.base import Embedder
from mote.models.registry import get_embedder
from mote.pipeline.embed import embed_images
from mote.pipeline.scan import RAW_EXTS, scan_folder
from mote.pipeline.signals import tone_signals
from mote.pipeline.thumbs import load_image
from PIL import Image

# --------------------------------------------------------------------------- photos


def sample_photos(root: Path, n: int, seed: int = 0, include_raw: bool = True) -> list[Path]:
    """Random sample of up to `n` photo paths under `root` (stable for a given seed)."""
    files = [f for f in scan_folder(Path(root).expanduser()) if include_raw or not f.is_raw]
    files.sort(key=lambda f: f.path)
    random.Random(seed).shuffle(files)
    return [Path(f.path) for f in files[:n]]


def _preview_path(cache_dir: Path, src: Path, size: int) -> Path:
    digest = hashlib.sha1(f"{src}|{src.stat().st_mtime}|{size}".encode()).hexdigest()
    return cache_dir / "previews" / str(size) / digest[:2] / f"{digest}.jpg"


def _make_preview(src: Path, dest: Path, size: int) -> Path | None:
    if dest.exists():
        return dest
    try:
        img = load_image(src, is_raw=src.suffix.lower() in RAW_EXTS)
        img.thumbnail((size, size), Image.Resampling.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest, "JPEG", quality=90)
        return dest
    except Exception as exc:  # unreadable file, missing RAW support, ...
        print(f"skip {src.name}: {type(exc).__name__}: {exc}")
        return None


def cache_previews(
    paths: Sequence[Path], cache_dir: Path, size: int = 512, workers: int = 8
) -> tuple[list[Path], list[Path]]:
    """Decode every photo once into a small JPEG preview. Returns (originals, previews)
    for the photos that could be read. Originals are only ever read."""
    dests = [_preview_path(cache_dir, p, size) for p in paths]
    with ThreadPoolExecutor(workers) as pool:
        done = list(pool.map(lambda a: _make_preview(*a, size), zip(paths, dests, strict=True)))
    kept = [(p, d) for p, d in zip(paths, done, strict=True) if d is not None]
    return [p for p, _ in kept], [d for _, d in kept]


class LazyImages(Sequence):
    """A Sequence of PIL images that loads previews from disk only when indexed."""

    def __init__(self, paths: Sequence[Path]):
        self.paths = list(paths)

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return [self._load(p) for p in self.paths[i]]
        return self._load(self.paths[i])

    @staticmethod
    def _load(p: Path) -> Image.Image:
        with Image.open(p) as im:
            return im.convert("RGB")


def tone_matrix(previews: Sequence[Path], cache_dir: Path) -> np.ndarray:
    """(N, 4) array of warmth, saturation, brightness, contrast, cached on disk."""
    key = hashlib.sha1("\n".join(map(str, previews)).encode()).hexdigest()[:16]
    path = cache_dir / "signals" / f"{key}.npy"
    if path.exists():
        return np.load(path)
    rows = []
    for p in previews:
        with Image.open(p) as im:
            s = tone_signals(np.asarray(im.convert("RGB").resize((128, 128))))
        rows.append([s.warmth, s.saturation, s.brightness, s.contrast])
    arr = np.asarray(rows, dtype=np.float32)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, arr)
    return arr


# --------------------------------------------------------------------------- models


@dataclass
class RunStats:
    model_id: str
    device: str = ""
    dim: int = 0
    params_m: float | None = None
    load_s: float = 0.0
    embed_s: float = 0.0
    images_per_s: float = 0.0
    peak_mem_gb: float | None = None
    license: str | None = None
    cached: bool = False
    error: str | None = None
    extra: dict = field(default_factory=dict)


def hf_license(model_id: str) -> str | None:
    if not model_id.startswith("hf:"):
        return None
    try:
        from huggingface_hub import model_info

        info = model_info(model_id.removeprefix("hf:"))
        card = info.card_data or {}
        return card.get("license") if isinstance(card, dict) else getattr(card, "license", None)
    except Exception:
        return None


def _peak_memory_gb(device: str) -> float | None:
    try:
        import torch

        if device == "cuda":
            return torch.cuda.max_memory_allocated() / 1e9
    except ImportError:
        pass
    try:
        import psutil

        return psutil.Process().memory_info().rss / 1e9
    except ImportError:
        return None


def _cache_file(cache_dir: Path, model_id: str, previews: Sequence[Path]) -> Path:
    key = hashlib.sha1("\n".join(map(str, previews)).encode()).hexdigest()[:16]
    safe = model_id.replace("/", "__").replace(":", "_")
    return cache_dir / "embeddings" / safe / f"{key}.npz"


def load_model(model_id: str) -> tuple[Embedder, float]:
    t0 = time.perf_counter()
    model = get_embedder(model_id)
    return model, time.perf_counter() - t0


def free_model(model: Embedder | None) -> None:
    del model
    gc.collect()
    try:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
    except ImportError:
        pass


def embed_previews(
    model_id: str,
    previews: Sequence[Path],
    cache_dir: Path,
    batch_size: int = 32,
    force: bool = False,
) -> tuple[np.ndarray | None, RunStats]:
    """Embed all previews with one model, using the on-disk cache when possible.

    The model is unloaded afterwards so the next one has the memory to itself.
    """
    stats = RunStats(model_id=model_id, license=hf_license(model_id))
    path = _cache_file(cache_dir, model_id, previews)
    if path.exists() and not force:
        data = np.load(path, allow_pickle=False)
        saved = json.loads(str(data["stats"]))
        saved.update(cached=True, license=stats.license or saved.get("license"))
        return data["vectors"], RunStats(**saved)

    model = None
    try:
        model, stats.load_s = load_model(model_id)
        stats.device, stats.dim = model.device, model.dim
        n_params = getattr(model, "num_parameters", None)
        stats.params_m = round(n_params / 1e6, 1) if n_params else None

        try:
            from tqdm.auto import tqdm

            bar = tqdm(total=len(previews), desc=model_id, leave=False)
            progress = lambda done: bar.update(done - bar.n)  # noqa: E731
        except ImportError:
            bar, progress = None, None

        t0 = time.perf_counter()
        vectors = embed_images(model, LazyImages(previews), batch_size, on_batch=progress)
        stats.embed_s = time.perf_counter() - t0
        if bar:
            bar.close()
        stats.images_per_s = round(len(previews) / max(stats.embed_s, 1e-9), 1)
        stats.peak_mem_gb = _peak_memory_gb(stats.device)
    except Exception as exc:
        stats.error = f"{type(exc).__name__}: {exc}"
        return None, stats
    finally:
        free_model(model)

    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, vectors=vectors, stats=json.dumps(asdict(stats)))
    return vectors, stats


def embed_texts(model_id: str, texts: list[str]) -> np.ndarray:
    """L2-normalised text embeddings (loads the model; text is cheap so no cache)."""
    model, _ = load_model(model_id)
    try:
        v = np.asarray(model.embed_text(texts), dtype=np.float32)
    finally:
        free_model(model)
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-12)


# --------------------------------------------------------------------------- metrics


def top_k(vectors: np.ndarray, query: np.ndarray, k: int = 8) -> list[int]:
    return np.argsort(-(vectors @ query))[:k].tolist()


def knn_accuracy(vectors: np.ndarray, labels: Sequence[str], k: int = 5) -> float:
    """Leave-one-out k-NN label accuracy: do a photo's nearest neighbours share its theme?"""
    labels = np.asarray(labels)
    sims = vectors @ vectors.T
    np.fill_diagonal(sims, -np.inf)
    nn = np.argsort(-sims, axis=1)[:, :k]
    correct = 0
    for i, row in enumerate(nn):
        values, counts = np.unique(labels[row], return_counts=True)
        correct += values[np.argmax(counts)] == labels[i]
    return correct / len(labels)


def zero_shot_accuracy(
    vectors: np.ndarray, labels: Sequence[str], text_vectors: np.ndarray, classes: list[str]
) -> float:
    """Classify each photo by its closest text prompt; tests image-text alignment."""
    pred = np.asarray(classes)[np.argmax(vectors @ text_vectors.T, axis=1)]
    return float(np.mean(pred == np.asarray(labels)))


def cluster_agreement(pred: np.ndarray, labels: Sequence[str]) -> dict[str, float]:
    from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score

    labels = np.asarray(labels)
    mask = pred != -1
    return {
        "nmi": normalized_mutual_info_score(labels, pred),
        "ari": adjusted_rand_score(labels, pred),
        "nmi_no_noise": normalized_mutual_info_score(labels[mask], pred[mask])
        if mask.sum() > 1
        else float("nan"),
    }


# --------------------------------------------------------------------------- plots


def show_grid(
    paths: Sequence[Path],
    titles: Sequence[str] | None = None,
    cols: int = 8,
    size: float = 1.8,
    suptitle: str | None = None,
):
    import matplotlib.pyplot as plt

    n = max(len(paths), 1)
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * size, rows * size), squeeze=False)
    for ax in axes.flat:
        ax.axis("off")
    for i, p in enumerate(paths):
        ax = axes.flat[i]
        with Image.open(p) as im:
            ax.imshow(im.convert("RGB"))
        if titles:
            ax.set_title(titles[i], fontsize=7)
    if suptitle:
        fig.suptitle(suptitle, fontsize=11, x=0.01, ha="left")
    fig.tight_layout()
    plt.show()
