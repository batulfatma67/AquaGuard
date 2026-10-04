
from __future__ import annotations

from functools import lru_cache

import numpy as np


EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load the embedding model once per Python process."""
    try:
        from sentence_transformers import SentenceTransformer
    except (ImportError, OSError) as exc:
        raise RuntimeError(
            "The local embedding model could not load. Windows Application Control "
            "may be blocking one of its native dependencies. Ask your administrator "
            "to approve the installed SciPy/PyTorch files, or use an approved Python environment."
        ) from exc

    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def embed_texts(texts: list[str]) -> np.ndarray:
    """Create normalized float32 embeddings for documents/chunks."""
    if not texts:
        raise ValueError("Cannot embed an empty text list.")

    model = get_embedding_model()

    vectors = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return np.asarray(vectors, dtype="float32")


def embed_query(query: str) -> np.ndarray:
    """Create one normalized query embedding."""
    if not query.strip():
        raise ValueError("Query cannot be empty.")

    model = get_embedding_model()

    vector = model.encode(
        [query],
        show_progress_bar=False,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    return np.asarray(vector, dtype="float32")
