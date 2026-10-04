from __future__ import annotations

from pathlib import Path

from .chunker import chunk_pages
from .groq_client import generate_answer
from .pdf_loader import extract_pdf_pages


def build_knowledge_base(
    uploaded_files,
    chunk_size: int = 900,
    chunk_overlap: int = 150,
) -> dict:
    """Extract, chunk, embed, and index one or more uploaded PDFs."""
    all_chunks: list[dict] = []
    errors: list[str] = []

    for uploaded_file in uploaded_files:
        try:
            pages = extract_pdf_pages(uploaded_file)
            chunks = chunk_pages(
                pages,
                source_name=Path(uploaded_file.name).name,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            all_chunks.extend(chunks)
        except Exception as exc:
            errors.append(f"{uploaded_file.name}: {exc}")

    if not all_chunks:
        raise ValueError(
            "No text chunks were created from the uploaded PDFs.\n"
            + "\n".join(f"- {item}" for item in errors)
        )

    from .embeddings import embed_texts
    from .vector_store import build_faiss_index

    embeddings = embed_texts([chunk["text"] for chunk in all_chunks])

    info = build_faiss_index(all_chunks, embeddings)
    info["skipped"] = errors
    return info


NOT_FOUND_MESSAGE = (
    "I could not find enough information in the uploaded documents to answer that."
)

# Cosine similarity below this is treated as "not in the knowledge base".
MIN_RELEVANCE = 0.25


def ask_rag(
    question: str,
    top_k: int = 4,
    min_score: float = MIN_RELEVANCE,
) -> tuple[str, list[dict]]:
    """Retrieve relevant chunks and generate a grounded Groq answer."""
    if not question.strip():
        raise ValueError("Please enter a question.")

    from .vector_store import search

    results = [r for r in search(question, top_k=top_k) if r["score"] >= min_score]

    if not results:
        return NOT_FOUND_MESSAGE, []

    context_parts = []

    for result in results:
        context_parts.append(
            f"[{result['source']}, p. {result['page']}]\n"
            f"{result['text']}"
        )

    context = "\n\n---\n\n".join(context_parts)

    answer = generate_answer(
        question=question,
        context=context,
    )

    return answer, results


def get_store_info() -> dict | None:
    """Load FAISS only when the RAG status view is requested."""
    from .vector_store import get_store_info as read_store_info

    return read_store_info()

