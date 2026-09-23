from __future__ import annotations

import json
from pathlib import Path

import faiss
import numpy as np

from .embeddings import embed_query


STORE_DIR = Path(__file__).resolve().parent.parent / "data" / "rag_store"
INDEX_PATH = STORE_DIR / "index.faiss"
METADATA_PATH = STORE_DIR / "metadata.json"


def build_faiss_index(chunks: list[dict], embeddings: np.ndarray) -> dict:
    """Build and persist a cosine-similarity FAISS index."""
    if not chunks:
        raise ValueError("No chunks were provided.")

    if embeddings.ndim != 2 or len(embeddings) != len(chunks):
        raise ValueError("Embedding count does not match chunk count.")

    STORE_DIR.mkdir(parents=True, exist_ok=True)

    vectors = np.ascontiguousarray(embeddings.astype("float32"))
    dimension = vectors.shape[1]

    # Because vectors are normalized, inner product is cosine similarity.
    index = faiss.IndexFlatIP(dimension)
    index.add(vectors)

    faiss.write_index(index, str(INDEX_PATH))

    metadata = {
        "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
        "dimension": dimension,
        "chunks": chunks,
        "documents": sorted({chunk["source"] for chunk in chunks}),
    }

    METADATA_PATH.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "documents": len(metadata["documents"]),
        "chunks": len(chunks),
        "dimension": dimension,
        "embedding_model": metadata["embedding_model"],
    }


def load_store() -> tuple[faiss.Index, dict]:
    """Load the persisted FAISS index and metadata."""
    if not INDEX_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError(
            "No knowledge base exists yet. Build the knowledge base first."
        )

    index = faiss.read_index(str(INDEX_PATH))
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))

    chunks = metadata.get("chunks", [])
    if index.ntotal != len(chunks):
        raise ValueError(
            "FAISS index and metadata are inconsistent. Rebuild the knowledge base."
        )

    return index, metadata


def search(query: str, top_k: int = 4) -> list[dict]:
    """Retrieve the most similar chunks for a query."""
    index, metadata = load_store()

    top_k = max(1, min(int(top_k), index.ntotal))

    query_vector = embed_query(query)
    scores, ids = index.search(query_vector, top_k)

    results: list[dict] = []

    for score, chunk_id in zip(scores[0], ids[0]):
        if chunk_id < 0:
            continue

        chunk = metadata["chunks"][int(chunk_id)].copy()
        chunk["score"] = float(score)
        results.append(chunk)

    return results


def get_store_info() -> dict | None:
    """Return lightweight knowledge-base information, or None if absent."""
    if not INDEX_PATH.exists() or not METADATA_PATH.exists():
        return None

    try:
        index, metadata = load_store()
    except Exception:
        return None

    return {
        "documents": len(metadata.get("documents", [])),
        "chunks": int(index.ntotal),
        "dimension": metadata.get("dimension"),
        "embedding_model": metadata.get("embedding_model"),
    }
