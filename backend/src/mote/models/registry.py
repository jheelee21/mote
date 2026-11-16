"""Look up embedders by id. Real models register here once chosen.

Factories are lazy so importing the registry never pulls in PyTorch.
"""

from __future__ import annotations

from collections.abc import Callable

from mote.models.base import Embedder

_FACTORIES: dict[str, Callable[[], Embedder]] = {}


def register(model_id: str, factory: Callable[[], Embedder]) -> None:
    if model_id in _FACTORIES:
        raise ValueError(f"embedder already registered: {model_id}")
    _FACTORIES[model_id] = factory


def available() -> list[str]:
    return sorted(_FACTORIES)


def get_embedder(model_id: str) -> Embedder:
    try:
        factory = _FACTORIES[model_id]
    except KeyError:
        raise ValueError(f"unknown embedder {model_id!r}; available: {available()}") from None
    return factory()


def _dummy() -> Embedder:
    from mote.models.dummy import DummyEmbedder

    return DummyEmbedder()


register("dummy", _dummy)

# Example for a real model, once chosen (lives in mote/models/<name>.py):
#
# def _openclip_b32() -> Embedder:
#     from mote.models.openclip import OpenClipEmbedder
#     return OpenClipEmbedder("ViT-B-32", "laion2b_s34b_b79k")
#
# register("openclip-vit-b-32", _openclip_b32)
