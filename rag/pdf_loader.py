from __future__ import annotations

from io import BytesIO
from typing import BinaryIO

import fitz


def extract_pdf_pages(file_obj: BinaryIO) -> list[dict]:
    """Extract text page-by-page from a PDF file-like object."""
    pdf_bytes = file_obj.getvalue() if hasattr(file_obj, "getvalue") else file_obj.read()
    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    pages: list[dict] = []

    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise ValueError(f"Could not open PDF: {exc}") from exc

    try:
        if document.page_count == 0:
            raise ValueError("The PDF contains no pages.")

        for page_number, page in enumerate(document, start=1):
            text = page.get_text("text") or ""
            text = _clean_text(text)

            if text:
                pages.append(
                    {
                        "page": page_number,
                        "text": text,
                    }
                )
    finally:
        document.close()

    if not pages:
        raise ValueError(
            "No selectable text was found. This PDF may be scanned/image-only. "
            "Add OCR before using it with this prototype."
        )

    return pages


def _clean_text(text: str) -> str:
    """Normalize common PDF extraction artifacts without changing wording."""
    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    lines = [line.strip() for line in text.split("\n")]
    cleaned_lines: list[str] = []

    for line in lines:
        if not line:
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            continue
        cleaned_lines.append(" ".join(line.split()))

    return "\n".join(cleaned_lines).strip()
