"""Group photos into candidate Stories.

Plan: concatenate semantic embeddings with weighted tone signals, reduce with
UMAP, cluster with HDBSCAN. Requires the `ml` extra.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ClusterParams:
    signal_weight: float = 0.3  # 0 = subject only, 1 = mood/tone heavy
    umap_neighbors: int = 15
    umap_components: int = 10
    min_cluster_size: int = 25
    seed: int = 0


def build_features(
    embeddings: np.ndarray, signals: np.ndarray, params: ClusterParams
) -> np.ndarray:
    """Standardise tone signals and append them, scaled by `signal_weight`."""
    if len(signals) == 0:
        return embeddings
    s = (signals - signals.mean(0)) / np.maximum(signals.std(0), 1e-6)
    return np.hstack([embeddings, s * params.signal_weight])


def cluster(features: np.ndarray, params: ClusterParams) -> np.ndarray:
    """Return a cluster label per row (-1 = noise). TODO: UMAP + HDBSCAN."""
    raise NotImplementedError
