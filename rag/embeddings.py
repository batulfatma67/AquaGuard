from functools import lru_cache

MODEL_NAME = "all-MiniLM-L6-v2"  # 384-dimensional (matches FAISSIndex default)


@lru_cache(maxsize=1)
def _get_model():
    """
    Load the embedding model only when it is first needed.

    Importing this file used to load the model immediately, which made every
    app start slow even when the index was loaded from the saved cache.
    """
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def get_embedding(text):
    embedding = _get_model().encode(text, convert_to_tensor=False)
    return embedding.tolist()


def embed_query(text):
    return get_embedding(text)


def get_embeddings_batch(texts, batch_size=64):
    if not texts:
        return []

    embeddings = _get_model().encode(
        texts,
        batch_size=batch_size,
        convert_to_tensor=False,
        show_progress_bar=False,
    )
    return embeddings.tolist()
