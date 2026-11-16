"""Name clusters by zero-shot scoring against a theme vocabulary."""

from __future__ import annotations

SUBJECTS = [
    "city street",
    "people",
    "portrait",
    "landscape",
    "forest",
    "coast",
    "architecture",
    "food",
    "interior",
    "night city",
    "mountains",
    "animals",
]
MOODS = [
    "quiet",
    "lonely",
    "busy",
    "warm",
    "cool",
    "moody",
    "bright",
    "foggy",
    "golden hour",
    "blue hour",
    "minimal",
    "nostalgic",
]


def theme_prompts() -> list[str]:
    """Candidate phrases to score each cluster centroid against."""
    return [f"a {m} photo of {s}" for s in SUBJECTS for m in MOODS]


def name_cluster(centroid, embedder) -> str:
    """TODO: embed `theme_prompts()` once, pick the best-scoring phrase, tidy it into a title."""
    raise NotImplementedError
