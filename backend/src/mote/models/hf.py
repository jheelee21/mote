"""Embedders for image-text models hosted on the Hugging Face Hub.

One adapter covers the two common ways these models are published:

- **transformers**: `CLIPModel`, `SiglipModel`, `Siglip2Model`, MetaCLIP, ... loaded
  with `AutoModel` + `AutoProcessor` (e.g. `openai/clip-vit-base-patch32`,
  `google/siglip2-base-patch16-224`).
- **open_clip**: repos that ship an `open_clip_config.json`
  (e.g. `laion/CLIP-ViT-B-32-laion2B-s34B-b79K`, `apple/DFN2B-CLIP-ViT-L-14`).

Use it through the registry with an `hf:` prefix::

    get_embedder("hf:google/siglip2-base-patch16-224")

Requires the `ml` extra. Weights download to the Hugging Face cache on first use;
that download is the only network access Mote makes.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Literal

import numpy as np
from PIL import Image

from mote.models.base import Embedder

Backend = Literal["auto", "transformers", "open_clip"]

# Models trained with fixed-length text (SigLIP family) must be padded to max length.
_MAX_LENGTH_PADDING = {"siglip", "siglip2"}


def pick_device(preferred: str | None = None) -> str:
    import torch

    if preferred:
        return preferred
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def detect_backend(repo_id: str) -> Backend:
    """open_clip if the repo ships an open_clip config, otherwise transformers."""
    try:
        from huggingface_hub import file_exists

        if file_exists(repo_id, "open_clip_config.json"):
            return "open_clip"
    except Exception:
        # Offline or hub unavailable: fall back to a cached open_clip config if present.
        try:
            from huggingface_hub import try_to_load_from_cache

            if isinstance(try_to_load_from_cache(repo_id, "open_clip_config.json"), str):
                return "open_clip"
        except Exception:
            pass
    return "transformers"


def _features(out):
    """`get_*_features` returns a tensor in most transformers versions, an output object in some."""
    import torch

    if isinstance(out, torch.Tensor):
        return out
    for name in ("image_embeds", "text_embeds", "pooler_output"):
        value = getattr(out, name, None)
        if value is not None:
            return value
    return out[0]


class HFEmbedder(Embedder):
    def __init__(
        self,
        repo_id: str,
        backend: Backend = "auto",
        device: str | None = None,
        revision: str | None = None,
    ) -> None:
        import torch

        self.repo_id = repo_id
        self.id = f"hf:{repo_id}"
        self.backend: Backend = detect_backend(repo_id) if backend == "auto" else backend
        self._device = pick_device(device)
        self._dtype = torch.float16 if self._device == "cuda" else torch.float32

        if self.backend == "open_clip":
            self._load_open_clip()
        else:
            self._load_transformers(revision)
        self.model.eval()

        self.dim = int(self.embed_text(["a photo"]).shape[1])

    # -- loading ---------------------------------------------------------------

    def _load_transformers(self, revision: str | None) -> None:
        from transformers import AutoModel, AutoProcessor

        self.model = AutoModel.from_pretrained(
            self.repo_id, revision=revision, torch_dtype=self._dtype
        ).to(self._device)
        self.processor = AutoProcessor.from_pretrained(self.repo_id, revision=revision)
        self.model_type = getattr(self.model.config, "model_type", "")

    def _load_open_clip(self) -> None:
        import open_clip

        hub = f"hf-hub:{self.repo_id}"
        model, preprocess = open_clip.create_model_from_pretrained(hub, device=self._device)
        self.model = model.to(dtype=self._dtype)
        self.preprocess = preprocess
        self.tokenizer = open_clip.get_tokenizer(hub)
        self.model_type = "open_clip"

    # -- Embedder API ------------------------------------------------------------

    @property
    def device(self) -> str:
        return self._device

    @property
    def num_parameters(self) -> int:
        return sum(p.numel() for p in self.model.parameters())

    def embed_images(self, images: Sequence[Image.Image]) -> np.ndarray:
        import torch

        rgb = [im.convert("RGB") for im in images]
        with torch.inference_mode():
            if self.backend == "open_clip":
                pixels = torch.stack([self.preprocess(im) for im in rgb])
                feats = self.model.encode_image(pixels.to(self._device, self._dtype))
            else:
                inputs = self.processor(images=rgb, return_tensors="pt")
                pixels = inputs["pixel_values"].to(self._device, self._dtype)
                extra = {k: v.to(self._device) for k, v in inputs.items() if k != "pixel_values"}
                feats = _features(self.model.get_image_features(pixel_values=pixels, **extra))
        return feats.float().cpu().numpy()

    def embed_text(self, texts: Sequence[str]) -> np.ndarray:
        import torch

        texts = list(texts)
        with torch.inference_mode():
            if self.backend == "open_clip":
                tokens = self.tokenizer(texts).to(self._device)
                feats = self.model.encode_text(tokens)
            else:
                padding = "max_length" if self.model_type in _MAX_LENGTH_PADDING else True
                kwargs = {"max_length": 64} if padding == "max_length" else {}
                inputs = self.processor(
                    text=texts, padding=padding, truncation=True, return_tensors="pt", **kwargs
                )
                inputs = {k: v.to(self._device) for k, v in inputs.items()}
                feats = _features(self.model.get_text_features(**inputs))
        return feats.float().cpu().numpy()
