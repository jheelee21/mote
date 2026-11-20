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
    """Return an embedder by registered id, or any Hub model as ``hf:<repo_id>``."""
    if model_id.startswith("hf:"):
        from mote.models.hf import HFEmbedder

        return HFEmbedder(model_id.removeprefix("hf:"))
    try:
        factory = _FACTORIES[model_id]
    except KeyError:
        raise ValueError(f"unknown embedder {model_id!r}; available: {available()}") from None
    return factory()


def _dummy() -> Embedder:
    from mote.models.dummy import DummyEmbedder

    return DummyEmbedder()


register("dummy", _dummy)

# Any Hugging Face image-text model works without registering it:
#     get_embedder("hf:google/siglip2-base-patch16-224")
# Register a short alias here once a default model is chosen, e.g.
#     register("default", lambda: get_embedder("hf:<chosen repo>"))
