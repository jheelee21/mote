"""A deterministic, dependency-free embedder for tests and UI development.

Images are embedded from their downscaled pixels and text from a hash, so the
results are stable but carry no real meaning. Never use it for real indexing.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence

import numpy as np
from PIL import Image

from mote.models.base import Embedder


class DummyEmbedder(Embedder):
    id = "dummy"
    dim = 64

    def __init__(self) -> None:
        rng = np.random.default_rng(0)
        self._proj = rng.standard_normal((8 * 8 * 3, self.dim)).astype(np.float32)

    def embed_images(self, images: Sequence[Image.Image]) -> np.ndarray:
        out = np.empty((len(images), self.dim), dtype=np.float32)
        for i, im in enumerate(images):
            small = np.asarray(im.convert("RGB").resize((8, 8)), dtype=np.float32) / 255.0
            out[i] = small.reshape(-1) @ self._proj
        return out

    def embed_text(self, texts: Sequence[str]) -> np.ndarray:
        out = np.empty((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            seed = int.from_bytes(hashlib.sha256(t.encode()).digest()[:8], "little")
            out[i] = np.random.default_rng(seed).standard_normal(self.dim)
        return out
