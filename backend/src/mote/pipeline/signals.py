"""Cheap, model-free image signals: palette and tone.

These capture "tone" and "mood" dimensions that semantic embeddings tend to
under-weight. Input is an RGB thumbnail as a uint8 array (H, W, 3).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ToneSignals:
    palette: list[str]  # dominant colours, most common first, as #rrggbb
    warmth: float  # -1 (cool/blue) .. 1 (warm/orange)
    saturation: float  # 0 .. 1
    brightness: float  # 0 .. 1
    contrast: float  # 0 .. 1 (std of luminance, scaled)


def _hex(rgb: np.ndarray) -> str:
    r, g, b = (round(float(v)) for v in rgb)
    return f"#{r:02x}{g:02x}{b:02x}"


def dominant_palette(pixels: np.ndarray, k: int = 5, iters: int = 10, seed: int = 0) -> list[str]:
    """Simple k-means in RGB on a pixel sample. Good enough for palette dots."""
    rng = np.random.default_rng(seed)
    flat = pixels.reshape(-1, 3).astype(np.float32)
    if len(flat) > 4096:
        flat = flat[rng.choice(len(flat), 4096, replace=False)]
    k = min(k, len(np.unique(flat, axis=0)))
    centers = flat[rng.choice(len(flat), k, replace=False)]
    for _ in range(iters):
        labels = np.argmin(((flat[:, None, :] - centers[None]) ** 2).sum(-1), axis=1)
        for j in range(k):
            members = flat[labels == j]
            if len(members):
                centers[j] = members.mean(axis=0)
    counts = np.bincount(labels, minlength=k)
    return [_hex(centers[j]) for j in np.argsort(-counts)]


def tone_signals(rgb: np.ndarray) -> ToneSignals:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("expected an (H, W, 3) RGB array")
    x = rgb.astype(np.float32) / 255.0
    r, g, b = x[..., 0], x[..., 1], x[..., 2]

    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    cmax, cmin = x.max(axis=2), x.min(axis=2)
    sat = np.where(cmax > 0, (cmax - cmin) / np.maximum(cmax, 1e-6), 0.0)
    warmth = float(np.clip((r - b).mean() * 2.0, -1.0, 1.0))

    return ToneSignals(
        palette=dominant_palette(rgb),
        warmth=warmth,
        saturation=float(sat.mean()),
        brightness=float(lum.mean()),
        contrast=float(np.clip(lum.std() * 2.0, 0.0, 1.0)),
    )
