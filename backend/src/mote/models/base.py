"""The Embedder interface every model must implement.

Mote needs a joint image-text embedding space (CLIP/SigLIP-style) so that
zero-shot cluster naming and natural-language search both work.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

import numpy as np
from PIL import Image


class Embedder(ABC):
    #: Stable id stored with every embedding, e.g. "openclip-vit-b-32-laion2b".
    id: str
    #: Embedding dimension.
    dim: int

    @abstractmethod
    def embed_images(self, images: Sequence[Image.Image]) -> np.ndarray:
        """Return an (N, dim) float array for RGB PIL images."""

    @abstractmethod
    def embed_text(self, texts: Sequence[str]) -> np.ndarray:
        """Return an (N, dim) float array in the same space as the images."""

    @property
    def device(self) -> str:
        return "cpu"
