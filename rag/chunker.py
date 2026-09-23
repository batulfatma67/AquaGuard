from __future__ import annotations

import re


def chunk_pages(
    pages: list[dict],
    source_name: str,
    chunk_size: int = 900,
    chunk_overlap: int = 150,
) -> list[dict]:
    """
    Create overlapping character-based chunks while preserving page/source metadata.

    The splitter prefers paragraph, line, sentence, and word boundaries before
    falling back to a hard character boundary.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")

    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be >= 0 and smaller than chunk_size.")

    chunks: list[dict] = []

    for page in pages:
        page_chunks = _split_text(
            page["text"],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for chunk_index, text in enumerate(page_chunks, start=1):
            cleaned = text.strip()
            if not cleaned:
                continue

            chunks.append(
                {
                    "text": cleaned,
                    "source": source_name,
                    "page": int(page["page"]),
                    "chunk_on_page": chunk_index,
                }
            )

    if not chunks:
        raise ValueError(f"No usable text chunks were created from {source_name}.")

    return chunks


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    text = text.strip()

    if len(text) <= chunk_size:
        return [text]

    separators = ["\n\n", "\n", ". ", "? ", "! ", "; ", ", ", " "]
    pieces = _recursive_split(text, separators, chunk_size)

    chunks: list[str] = []
    current = ""

    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue

        candidate = f"{current} {piece}".strip() if current else piece

        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)

        overlap = _tail_overlap(current, chunk_overlap)
        candidate = f"{overlap} {piece}".strip() if overlap else piece

        if len(candidate) <= chunk_size:
            current = candidate
        else:
            # The recursive splitter can still produce a long atomic piece.
            hard_parts = _hard_split(candidate, chunk_size)
            chunks.extend(hard_parts[:-1])
            current = hard_parts[-1] if hard_parts else ""

    if current:
        chunks.append(current)

    # De-duplicate accidental exact repetitions.
    result: list[str] = []
    for chunk in chunks:
        if not result or chunk != result[-1]:
            result.append(chunk)

    return result


def _recursive_split(text: str, separators: list[str], chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    if not separators:
        return _hard_split(text, chunk_size)

    separator = separators[0]
    pieces = text.split(separator)

    if len(pieces) == 1:
        return _recursive_split(text, separators[1:], chunk_size)

    result: list[str] = []

    for piece in pieces:
        piece = piece.strip()
        if not piece:
            continue

        if len(piece) <= chunk_size:
            result.append(piece)
        else:
            result.extend(
                _recursive_split(piece, separators[1:], chunk_size)
            )

    return result


def _hard_split(text: str, chunk_size: int) -> list[str]:
    return [
        text[start : start + chunk_size]
        for start in range(0, len(text), chunk_size)
    ]


def _tail_overlap(text: str, overlap: int) -> str:
    if not text or overlap <= 0:
        return ""

    tail = text[-overlap:]

    # Prefer starting at a word boundary.
    match = re.search(r"\s", tail)
    if match:
        tail = tail[match.end() :]

    return tail.strip()

