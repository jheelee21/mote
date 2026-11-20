import numpy as np
import pytest

from mote.models.registry import get_embedder
from mote.pipeline.cluster import ClusterParams, build_features, centroids, cluster, cohesion
from mote.pipeline.naming import build_vocabulary, name_cluster, title_from_prompt

pytest.importorskip("sklearn")


def _blobs(seed=0):
    rng = np.random.default_rng(seed)
    centers = rng.standard_normal((3, 32))
    x = np.vstack([c + 0.05 * rng.standard_normal((40, 32)) for c in centers])
    return (x / np.linalg.norm(x, axis=1, keepdims=True)).astype(np.float32)


def test_cluster_finds_separated_groups():
    x = _blobs()
    labels = cluster(x, ClusterParams(umap_components=0, min_cluster_size=10))
    assert len(set(labels.tolist()) - {-1}) == 3
    assert cohesion(x, labels) > 0.9


def test_build_features_appends_weighted_signals():
    x = _blobs()
    signals = np.random.default_rng(1).random((len(x), 4))
    assert build_features(x, signals, ClusterParams(signal_weight=0)).shape == x.shape
    assert build_features(x, signals, ClusterParams(signal_weight=0.5)).shape == (len(x), 36)


def test_title_from_prompt():
    assert title_from_prompt("a foggy photo of a forest") == "Foggy forest"
    assert title_from_prompt("a blue hour photo of the city at night") == "Blue hour city at night"


def test_name_cluster_returns_ranked_titles():
    emb = get_embedder("dummy")
    vocab = build_vocabulary(emb, ["a quiet photo of a forest", "a busy photo of a market"])
    target = vocab.vectors[1]
    names = name_cluster(target, vocab, top_k=2)
    assert names[0][0] == "Busy market"
    assert names[0][1] >= names[1][1]


def test_centroids_skip_noise():
    x = _blobs()
    labels = np.array([0] * 40 + [1] * 40 + [-1] * 40)
    assert set(centroids(x, labels)) == {0, 1}
