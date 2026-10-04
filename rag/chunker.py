import re


def _clean(text):
    """Collapse line breaks / repeated spaces left over from PDF extraction."""
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(documents, max_chars=1000, overlap=200):
    """
    Split each page into overlapping chunks.

    Compared with a plain fixed-width split:
      - text is cleaned first (no stray line breaks / blank pages),
      - chunks end on a space instead of cutting words in half,
      - no tiny duplicate chunk is created at the end of a page.
    """
    if overlap >= max_chars:
        overlap = max_chars // 5

    chunked_docs = []

    for doc in documents:
        text = _clean(doc["chunk_text"])
        filename = doc["filename"]
        page_number = doc["page_number"]

        if not text:
            continue

        length = len(text)

        if length <= max_chars:
            chunked_docs.append({
                "filename": filename,
                "page_number": page_number,
                "chunk_text": text,
            })
            continue

        start = 0

        while start < length:
            end = min(start + max_chars, length)

            # Prefer to finish the chunk at a word boundary.
            if end < length:
                space = text.rfind(" ", start + int(max_chars * 0.8), end)
                if space != -1:
                    end = space

            chunk_str = text[start:end].strip()

            if chunk_str:
                chunked_docs.append({
                    "filename": filename,
                    "page_number": page_number,
                    "chunk_text": chunk_str,
                })

            if end >= length:
                break

            next_start = end - overlap
            start = next_start if next_start > start else end

    return chunked_docs
