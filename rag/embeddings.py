from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text):
    embedding = model.encode(text, convert_to_tensor=False)
    return embedding.tolist()

def embed_query(text):
    return get_embedding(text)

def get_embeddings_batch(texts):
    embeddings = model.encode(texts, convert_to_tensor=False, show_progress_bar=False)
    return embeddings.tolist()