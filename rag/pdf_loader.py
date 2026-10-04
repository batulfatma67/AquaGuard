from __future__ import annotations

from pathlib import Path


def extract_pdf_pages(pdf_source) -> list[dict]:
    try:
        import fitz
    except (ImportError, OSError) as exc:
        raise RuntimeError("PyMuPDF is required. Install with: pip install pymupdf") from exc

    if hasattr(pdf_source, "getvalue"):
        data = pdf_source.getvalue()
        filename = Path(getattr(pdf_source, "name", "document.pdf")).name
        if not data:
            raise ValueError(f"{filename} is empty.")
        doc = fitz.open(stream=data, filetype="pdf")
    else:
        path = Path(pdf_source)
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")
        filename = path.name
        doc = fitz.open(str(path))

    pages = []
    try:
        for i in range(len(doc)):
            text = (doc[i].get_text("text") or "").strip()
            if text:
                pages.append({"text": text, "page": i + 1})
    finally:
        doc.close()

    if not pages:
        raise ValueError(f"No extractable text was found in {filename}.")
    return pages


def load_and_extract_pdf(pdf_path):
    pages = extract_pdf_pages(pdf_path)
    filename = Path(getattr(pdf_path, "name", pdf_path)).name
    return [{"filename": filename, "page_number": p["page"], "chunk_text": p["text"]} for p in pages]
