import os
import glob
from rag.pdf_loader import load_and_extract_pdf
from rag.chunker import chunk_text
from rag.embeddings import get_embeddings_batch, get_embedding
from rag.vector_store import FAISSIndex
from rag.groq_client import get_grounded_answer

global_vector_store = FAISSIndex()
is_kb_built = False

def build_knowledge_base(data_folder=None):
    global is_kb_built
    
    # Automatically locate the data folder using absolute path
    if data_folder is None or not os.path.exists(str(data_folder)):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_folder = os.path.join(base_dir, "data")
        
    pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))
    
    # Fallback to direct path if relative path fails
    if not pdf_files:
        data_folder = r"C:\Users\DELL\Documents\AquaGuard\data"
        pdf_files = glob.glob(os.path.join(data_folder, "*.pdf"))
    
    if not pdf_files:
        return False, f"No PDF files found in path: {data_folder}. Please check folder."

    total_chunks = 0
    for file_path in pdf_files:
        docs = load_and_extract_pdf(file_path)
        if docs:
            chunks = chunk_text(docs)
            texts = [c["chunk_text"] for c in chunks]
            embeddings = get_embeddings_batch(texts)
            global_vector_store.add_chunks(chunks, embeddings)
            total_chunks += len(chunks)
    
    if total_chunks > 0:
        is_kb_built = True
        return True, f"Knowledge base successfully built with {total_chunks} passages from {len(pdf_files)} documents."
    else:
        return False, "Failed to extract text from PDFs."

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
    return answer, list(set(sources))

def get_store_info():
    return {"total_chunks": len(global_vector_store.metadata), "is_built": is_kb_built}