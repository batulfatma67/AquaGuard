import os
import fitz  # PyMuPDF

def load_and_extract_pdf(pdf_path):
    extracted_docs = []
    try:
        doc = fitz.open(pdf_path)
        filename = os.path.basename(pdf_path)
        
        for page_index in range(len(doc)):
            page = doc[page_index]
            text = page.get_text()
            
            if text.strip():
                extracted_docs.append({
                    "filename": filename,
                    "page_number": page_index + 1,
                    "chunk_text": text
                })
        doc.close()
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        
    return extracted_docs



