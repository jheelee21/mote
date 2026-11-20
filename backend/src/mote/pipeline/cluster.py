"""Group photos into candidate Stories.

Semantic embeddings are concatenated with weighted tone signals, reduced with
UMAP (falls back to PCA if umap-learn is missing) and clustered with HDBSCAN
from scikit-learn. Requires the `ml` extra.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ClusterParams:
    signal_weight: float = 0.3  # 0 = subject only, higher = more mood/tone
    umap_neighbors: int = 15
    umap_components: int = 10  # 0 = cluster the raw features
    min_cluster_size: int = 25
    min_samples: int | None = None
    seed: int = 0


def build_features(
    embeddings: np.ndarray, signals: np.ndarray, params: ClusterParams
) -> np.ndarray:
    """Standardise tone signals and append them, scaled by `signal_weight`.

    Embeddings are L2-normalised, so each signal column ends up on a comparable
    scale to the whole embedding once multiplied by `signal_weight`.
    """
    if len(signals) == 0 or params.signal_weight == 0:
        return embeddings
    s = (signals - signals.mean(0)) / np.maximum(signals.std(0), 1e-6)
    s = s / np.sqrt(s.shape[1])
    return np.hstack([embeddings, s * params.signal_weight]).astype(np.float32)


def reduce(features: np.ndarray, params: ClusterParams) -> np.ndarray:
    n = len(features)
    k = params.umap_components
    if k == 0 or n <= k + 2:
        return features
    try:
        import umap

        return umap.UMAP(
            n_neighbors=min(params.umap_neighbors, n - 1),
            n_components=k,
            metric="cosine",
            min_dist=0.0,
            random_state=params.seed,
        ).fit_transform(features)
    except ImportError:
        from sklearn.decomposition import PCA

        return PCA(n_components=min(k, features.shape[1]), random_state=params.seed).fit_transform(
            features
        )


def cluster(features: np.ndarray, params: ClusterParams) -> np.ndarray:
    """Return a cluster label per row; -1 means noise (not in any Story)."""
    from sklearn.cluster import HDBSCAN

    if len(features) < max(params.min_cluster_size, 2):
        return np.full(len(features), -1, dtype=int)
    x = reduce(features, params)
    return HDBSCAN(
        min_cluster_size=params.min_cluster_size,
        min_samples=params.min_samples,
        copy=True,
    ).fit_predict(x)


def centroids(embeddings: np.ndarray, labels: np.ndarray) -> dict[int, np.ndarray]:
    """L2-normalised mean embedding of every non-noise cluster."""
    out = {}
    for label in sorted(set(labels.tolist()) - {-1}):
        c = embeddings[labels == label].mean(axis=0)
        out[label] = c / max(float(np.linalg.norm(c)), 1e-12)
    return out


def cohesion(embeddings: np.ndarray, labels: np.ndarray) -> float:
    """Mean cosine similarity of members to their cluster centroid (higher = tighter)."""
    cents = centroids(embeddings, labels)
    if not cents:
        return float("nan")
    sims = [float((embeddings[labels == k] @ c).mean()) for k, c in cents.items()]
    return float(np.mean(sims))
