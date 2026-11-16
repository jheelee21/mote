"""Batch images through an Embedder and serialise vectors for storage."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Sequence

import numpy as np
from PIL import Image

from mote.models.base import Embedder


def batched(items: Sequence, size: int) -> Iterator[Sequence]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def embed_images(
    embedder: Embedder,
    images: Sequence[Image.Image],
    batch_size: int = 32,
    on_batch: Callable[[int], None] | None = None,
) -> np.ndarray:
    """Return an (N, dim) float32 array of L2-normalised embeddings."""
    out = []
    done = 0
    for batch in batched(images, batch_size):
        vecs = np.asarray(embedder.embed_images(list(batch)), dtype=np.float32)
        out.append(vecs)
        done += len(batch)
        if on_batch:
            on_batch(done)
    if not out:
        return np.zeros((0, embedder.dim), dtype=np.float32)
    return l2_normalise(np.concatenate(out))


def l2_normalise(x: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / np.maximum(norms, 1e-12)


def to_blob(vec: np.ndarray) -> bytes:
    return np.asarray(vec, dtype="<f4").tobytes()


def from_blob(blob: bytes, dim: int) -> np.ndarray:
    arr = np.frombuffer(blob, dtype="<f4")
    if arr.size != dim:
        raise ValueError(f"expected {dim} floats, got {arr.size}")
    return arr


def cosine_search(query: np.ndarray, matrix: np.ndarray, k: int = 50) -> list[tuple[int, float]]:
    """Top-k (row index, score) by cosine similarity; both inputs L2-normalised."""
    if matrix.size == 0:
        return []
    scores = matrix @ query
    k = min(k, len(scores))
    idx = np.argpartition(-scores, k - 1)[:k]
    idx = idx[np.argsort(-scores[idx])]
    return [(int(i), float(scores[i])) for i in idx]


def stack(vectors: Iterable[np.ndarray]) -> np.ndarray:
    vs = list(vectors)
    return np.stack(vs).astype(np.float32) if vs else np.zeros((0, 0), dtype=np.float32)
