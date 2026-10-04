def chunk_text(documents, max_chars=1000, overlap=200):
    chunked_docs = []
    
    for doc in documents:
        text = doc["chunk_text"]
        filename = doc["filename"]
        page_number = doc["page_number"]
        
        start = 0
        text_length = len(text)
        
        if text_length <= max_chars:
            chunked_docs.append({
                "filename": filename,
                "page_number": page_number,
                "chunk_text": text
            })
            continue
            
        while start < text_length:
            end = start + max_chars
            chunk_str = text[start:end]
            
            chunked_docs.append({
                "filename": filename,
                "page_number": page_number,
                "chunk_text": chunk_str
            })
            
            start += (max_chars - overlap)
            
    return chunked_docs