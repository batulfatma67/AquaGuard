from functools import lru_cache

MODEL_NAME = "all-MiniLM-L6-v2"  # 384-dimensional (matches FAISSIndex default)


@lru_cache(maxsize=1)
def _get_model():
    """
    Load the embedding model only when it is first needed.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def get_embedding(text):
    """Generate an embedding for a single text."""
    embedding = _get_model().encode(
        text,
        convert_to_tensor=False,
    )
    return embedding.tolist()


def embed_query(text):
    """Generate an embedding for a user query."""
    return get_embedding(text)


def get_embeddings_batch(texts, batch_size=64):
    """Generate embeddings for multiple text chunks."""
    if not texts:
        return []

    embeddings = _get_model().encode(
        texts,
        batch_size=batch_size,
        convert_to_tensor=False,
        show_progress_bar=False,
    )

    return embeddings.tolist()


def embed_texts(texts, batch_size=64):
    """
    Compatibility wrapper used by the RAG knowledge-base pipeline.

    The pipeline expects embed_texts(), while the underlying implementation
    uses get_embeddings_batch().
    """
    return get_embeddings_batch(texts, batch_size=batch_size)
