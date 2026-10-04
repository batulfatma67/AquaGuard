import os
import pymupdf


def load_and_extract_pdf(pdf_path):
    extracted_docs = []

    try:
        doc = pymupdf.open(pdf_path)
        filename = os.path.basename(pdf_path)

        for page_index, page in enumerate(doc):
            text = page.get_text("text")

            if text and text.strip():
                extracted_docs.append({
                    "filename": filename,
                    "page_number": page_index + 1,
                    "chunk_text": text.strip()
                })

        doc.close()

    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

    return extracted_docs
