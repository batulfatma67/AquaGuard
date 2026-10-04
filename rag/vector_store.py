import numpy as np
import faiss

class FAISSIndex:
    def __init__(self, dimension=384):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.metadata = []

    def add_chunks(self, chunks, embeddings):
        if not embeddings:
            return
        vectors = np.array(embeddings).astype('float32')
        self.index.add(vectors)
        self.metadata.extend(chunks)

    def search(self, query_embedding, k=3):
        if self.index.ntotal == 0:
            return []
        vector = np.array([query_embedding]).astype('float32')
        distances, indices = self.index.search(vector, min(k, self.index.ntotal))
        
        results = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx != -1 and idx < len(self.metadata):
                results.append({
                    "chunk": self.metadata[idx],
                    "score": float(dist)
                })
        return results