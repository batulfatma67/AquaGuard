import os
import glob
import pickle
import threading

from rag.pdf_loader import load_and_extract_pdf
from rag.chunker import chunk_text
from rag.embeddings import get_embeddings_batch, get_embedding
from rag.vector_store import FAISSIndex
from rag.groq_client import get_grounded_answer

global_vector_store = FAISSIndex()
is_kb_built = False
kb_doc_count = 0

# Prevents two browser sessions from building the index at the same time.
_build_lock = threading.Lock()

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Embeddings are saved here after the first build. If the PDFs have not
# changed, the next start loads this file instead of re-embedding everything.
_CACHE_FILE = os.path.join(_BASE_DIR, "rag_cache", "kb_cache.pkl")
_CACHE_VERSION = 2  # bump whenever chunking or the embedding model changes


def _resolve_pdf_files(data_folder):
    # Automatically locate the data folder using absolute path
    if data_folder is None or not os.path.exists(str(data_folder)):
        data_folder = os.path.join(_BASE_DIR, "data")

    pdf_files = sorted(glob.glob(os.path.join(data_folder, "*.pdf")))

    # Fallback to direct path if relative path fails
    if not pdf_files:
        data_folder = r"C:\Users\DELL\Documents\AquaGuard\data"
        pdf_files = sorted(glob.glob(os.path.join(data_folder, "*.pdf")))

    return data_folder, pdf_files


def _signature(pdf_files):
    # Name + size only (modified time changes on every git clone).
    return [(os.path.basename(p), os.path.getsize(p)) for p in pdf_files]


def _load_cache(signature):
    try:
        with open(_CACHE_FILE, "rb") as f:
            cached = pickle.load(f)
        if (
            cached.get("version") == _CACHE_VERSION
            and cached.get("signature") == signature
        ):
            return cached["parts"]
    except Exception:
        pass
    return None


def _save_cache(signature, parts):
    try:
        os.makedirs(os.path.dirname(_CACHE_FILE), exist_ok=True)
        with open(_CACHE_FILE, "wb") as f:
            pickle.dump(
                {
                    "version": _CACHE_VERSION,
                    "signature": signature,
                    "parts": parts,
                },
                f,
                protocol=pickle.HIGHEST_PROTOCOL,
            )
    except Exception:
        pass  # a cache failure must never break the app


def build_knowledge_base(data_folder=None, force=False):
    """
    Build (or load from cache) the knowledge base from the PDFs in data/.

    force=False: if the index is already in memory, return immediately.
    force=True : ignore memory and cache, re-read and re-embed every PDF.
    Returns (success: bool, message: str).
    """
    global global_vector_store, is_kb_built, kb_doc_count

    with _build_lock:
        if is_kb_built and not force:
            return True, "Knowledge base is already built."

        data_folder, pdf_files = _resolve_pdf_files(data_folder)

        if not pdf_files:
            return False, f"No PDF files found in path: {data_folder}. Please check folder."

        signature = _signature(pdf_files)

        parts = None if force else _load_cache(signature)
        from_cache = parts is not None

        if parts is None:
            parts = []
            for file_path in pdf_files:
                docs = load_and_extract_pdf(file_path)
                if not docs:
                    continue

                chunks = chunk_text(docs)
                if not chunks:
                    continue

                texts = [c["chunk_text"] for c in chunks]
                embeddings = get_embeddings_batch(texts)
                parts.append((chunks, embeddings))

        total_chunks = sum(len(chunks) for chunks, _ in parts)

        if total_chunks == 0:
            return False, "Failed to extract text from PDFs."

        # Always start from a fresh index so rebuilding never duplicates chunks.
        new_store = FAISSIndex()
        for chunks, embeddings in parts:
            new_store.add_chunks(chunks, embeddings)

        global_vector_store = new_store
        is_kb_built = True
        kb_doc_count = len(parts)

        if not from_cache:
            _save_cache(signature, parts)

        how = "loaded from cache" if from_cache else "built"
        return True, (
            f"Knowledge base successfully {how} with {total_chunks} passages "
            f"from {len(parts)} documents."
        )


def ask_rag(query, top_k=3):
    if not is_kb_built:
        return "Knowledge base is not initialized. Please build the knowledge base first.", []

    query_emb = get_embedding(query)
    results = global_vector_store.search(query_emb, k=top_k)

    if not results:
        return "The knowledge base does not contain an answer to this question.", []

    context_text = ""
    sources = []

    for res in results:
        chunk = res["chunk"]
        context_text += f"[Source: {chunk['filename']}, Page: {chunk['page_number']}]\n{chunk['chunk_text']}\n\n"
        sources.append(f"{chunk['filename']} (Page {chunk['page_number']})")

    answer = get_grounded_answer(query, context_text)
    return answer, sorted(set(sources))


def get_store_info():
    total = len(global_vector_store.metadata)
    return {
        "total_chunks": total,
        "chunks": total,
        "documents": kb_doc_count,
        "is_built": is_kb_built,
    }
