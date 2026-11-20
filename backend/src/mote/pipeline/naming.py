"""Name clusters by zero-shot scoring against a theme vocabulary.

The embedder turns every candidate phrase into a text vector once; each
cluster centroid is then matched against those vectors.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SUBJECTS = [
    "a city street",
    "people in the city",
    "a portrait",
    "a landscape",
    "a forest",
    "the coast",
    "architecture",
    "food",
    "an interior",
    "the city at night",
    "mountains",
    "animals",
    "a beach",
    "a market",
    "a cafe",
    "a concert",
]
MOODS = [
    "quiet",
    "lonely",
    "busy",
    "warm",
    "cool-toned",
    "moody",
    "bright",
    "foggy",
    "golden hour",
    "blue hour",
    "minimal",
    "nostalgic",
    "rainy",
    "snowy",
]


def theme_prompts(subjects: list[str] | None = None, moods: list[str] | None = None) -> list[str]:
    """Candidate phrases to score each cluster centroid against."""
    subjects = subjects or SUBJECTS
    moods = moods or MOODS
    return [f"a {m} photo of {s}" for s in subjects for m in moods]


@dataclass(frozen=True)
class ThemeVocabulary:
    prompts: list[str]
    vectors: np.ndarray  # (len(prompts), dim), L2-normalised


def build_vocabulary(embedder, prompts: list[str] | None = None) -> ThemeVocabulary:
    prompts = prompts or theme_prompts()
    vecs = np.asarray(embedder.embed_text(prompts), dtype=np.float32)
    vecs /= np.maximum(np.linalg.norm(vecs, axis=1, keepdims=True), 1e-12)
    return ThemeVocabulary(prompts, vecs)


def title_from_prompt(prompt: str) -> str:
    """'a foggy photo of a forest' -> 'Foggy forest'."""
    mood, _, subject = prompt.removeprefix("a ").partition(" photo of ")
    for article in ("a ", "an ", "the "):
        subject = subject.removeprefix(article)
    text = f"{mood} {subject}".strip()
    return text[:1].upper() + text[1:]


def name_cluster(
    centroid: np.ndarray, vocab: ThemeVocabulary, top_k: int = 3
) -> list[tuple[str, float]]:
    """Best `top_k` (title, score) pairs for an L2-normalised centroid."""
    scores = vocab.vectors @ centroid
    best = np.argsort(-scores)[:top_k]
    return [(title_from_prompt(vocab.prompts[i]), float(scores[i])) for i in best]
