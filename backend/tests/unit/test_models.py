import numpy as np
import pytest
from PIL import Image

from mote.models.registry import available, get_embedder
from mote.pipeline.embed import cosine_search, embed_images, from_blob, to_blob


def test_registry_has_dummy_and_rejects_unknown():
    assert "dummy" in available()
    with pytest.raises(ValueError):
        get_embedder("does-not-exist")


def test_embed_roundtrip_and_search():
    emb = get_embedder("dummy")
    imgs = [Image.new("RGB", (32, 32), c) for c in [(10, 20, 200), (200, 120, 30), (12, 22, 198)]]
    vecs = embed_images(emb, imgs, batch_size=2)
    assert vecs.shape == (3, emb.dim)
    assert np.allclose(np.linalg.norm(vecs, axis=1), 1.0, atol=1e-5)

    assert np.allclose(from_blob(to_blob(vecs[0]), emb.dim), vecs[0])

    top = cosine_search(vecs[0], vecs, k=2)
    assert top[0][0] == 0
    assert top[1][0] == 2  # the near-identical blue image
