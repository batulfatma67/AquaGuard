from __future__ import annotations

import json
from pathlib import Path
from .embeddings import embed_query

STORE_DIR = Path(__file__).resolve().parent.parent / "data" / "rag_store"
INDEX_PATH = STORE_DIR / "index.faiss"
METADATA_PATH = STORE_DIR / "metadata.json"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _load_faiss():
    try:
        import faiss
        import numpy as np
        return faiss, np
    except (ImportError, OSError) as exc:
        raise RuntimeError("FAISS could not load. Check your FAISS installation.") from exc


def build_faiss_index(chunks, embeddings) -> dict:
    faiss, np = _load_faiss()
    if not chunks:
        raise ValueError("No chunks were provided.")
    vectors = np.asarray(embeddings, dtype="float32")
    if vectors.ndim != 2 or len(vectors) != len(chunks):
        raise ValueError("Embeddings must be a 2D array matching the chunks.")
    if vectors.shape[1] == 0 or not np.isfinite(vectors).all():
        raise ValueError("Embeddings contain invalid values.")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("One or more embeddings have zero length.")
    vectors = np.ascontiguousarray(vectors / norms, dtype="float32")
    dimension = vectors.shape[1]
    STORE_DIR.mkdir(parents=True, exist_ok=True)
    index = faiss.IndexFlatIP(dimension)
    index.add(vectors)
    faiss.write_index(index, str(INDEX_PATH))
    metadata = {
        "embedding_model": EMBEDDING_MODEL,
        "dimension": dimension,
        "chunks": chunks,
        "documents": sorted({c.get("source", "unknown") for c in chunks}),
    }
    METADATA_PATH.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"documents": len(metadata["documents"]), "chunks": len(chunks), "dimension": dimension,
            "embedding_model": EMBEDDING_MODEL}


def load_store():
    faiss, _ = _load_faiss()
    if not INDEX_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError("No knowledge base exists yet. Build the knowledge base first.")
    index = faiss.read_index(str(INDEX_PATH))
    metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    if index.ntotal != len(metadata.get("chunks", [])):
        raise ValueError("FAISS index and metadata are inconsistent.")
    if index.d != metadata.get("dimension"):
        raise ValueError("FAISS index dimension does not match metadata.")
    return index, metadata


def search(query: str, top_k: int = 4) -> list[dict]:
    index, metadata = load_store()
    if index.ntotal == 0 or top_k <= 0:
        return []
    query_vector = embed_query(query)
    _, np = _load_faiss()
    query_vector = np.asarray(query_vector, dtype="float32")
    if query_vector.ndim == 1:
        query_vector = query_vector.reshape(1, -1)
    if query_vector.shape != (1, index.d):
        raise ValueError("Query embedding dimension does not match FAISS index.")
    norm = np.linalg.norm(query_vector)
    if norm == 0 or not np.isfinite(norm):
        raise ValueError("Query embedding is invalid.")
    query_vector = np.ascontiguousarray(query_vector / norm, dtype="float32")
    scores, ids = index.search(query_vector, min(int(top_k), index.ntotal))
    results = []
    for score, chunk_id in zip(scores[0], ids[0]):
        if chunk_id >= 0:
            chunk = metadata["chunks"][int(chunk_id)].copy()
            chunk["score"] = float(score)
            results.append(chunk)
    return results


def get_store_info() -> dict | None:
    if not INDEX_PATH.exists() or not METADATA_PATH.exists():
        return None
    try:
        index, metadata = load_store()
    except Exception:
        return None
    return {"documents": len(metadata.get("documents", [])), "chunks": int(index.ntotal),
            "dimension": metadata.get("dimension"), "embedding_model": metadata.get("embedding_model")}


class FAISSIndex:
    """Compatibility wrapper for older project imports."""
    def __init__(self):
        self.index, self.metadata = load_store()
        self.chunks = self.metadata.get("chunks", [])

    def search(self, query_embedding, k: int = 3) -> list[dict]:
        if self.index.ntotal == 0 or k <= 0:
            return []
        _, np = _load_faiss()
        vector = np.asarray(query_embedding, dtype="float32")
        if vector.ndim == 1:
            vector = vector.reshape(1, -1)
        if vector.shape != (1, self.index.d):
            raise ValueError("Query embedding dimension does not match FAISS index.")
        norm = np.linalg.norm(vector)
        if norm == 0 or not np.isfinite(norm):
            raise ValueError("Query embedding is invalid.")
        vector = np.ascontiguousarray(vector / norm, dtype="float32")
        scores, ids = self.index.search(vector, min(int(k), self.index.ntotal))
        return [{"chunk": self.chunks[int(i)], "score": float(s)} for s, i in zip(scores[0], ids[0]) if i >= 0]
