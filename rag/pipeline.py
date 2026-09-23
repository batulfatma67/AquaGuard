from __future__ import annotations

from pathlib import Path

from .chunker import chunk_pages
from .embeddings import embed_texts
from .groq_client import generate_answer
from .pdf_loader import extract_pdf_pages
from .vector_store import build_faiss_index, get_store_info, search


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

    if errors:
        error_text = "\n".join(f"- {item}" for item in errors)
        raise ValueError(
            "One or more PDFs could not be processed:\n" + error_text
        )

    if not all_chunks:
        raise ValueError("No text chunks were created from the uploaded PDFs.")

    embeddings = embed_texts([chunk["text"] for chunk in all_chunks])

    info = build_faiss_index(all_chunks, embeddings)
    return info


def ask_rag(question: str, top_k: int = 4) -> tuple[str, list[dict]]:
    """Retrieve relevant chunks and generate a grounded Groq answer."""
    results = search(question, top_k=top_k)

    if not results:
        raise ValueError("No relevant document passages were retrieved.")

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

