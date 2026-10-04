# AquaGuard
# AquaGuard AI + Document RAG

This version keeps the existing AquaGuard farm-water prototype and adds a PDF-based Retrieval-Augmented Generation (RAG) workspace.

## RAG pipeline

PDF upload → PyMuPDF text extraction → page-aware overlapping chunks → Sentence Transformers embeddings → FAISS cosine-similarity retrieval → Groq grounded answer with source/page references.

## Project structure

```text
app.py                  # thin entrypoint: styles, sidebar navigation, page routing
config.py               # paths, option lists, default input assumptions
ui/                     # styles.py, state.py, components.py, pages/ (one module per page)
engine/                 # water_engine.py (account), scenario_engine.py, reference_data.py
rag/                    # pdf_loader, chunker, embeddings, vector_store, groq_client, pipeline
agent/agent_router.py   # experimental tool router (calculate / compare / search / report)
services/report_service.py
database/db.py          # SQLite: farms, water_accounts, scenarios, reports (auto-migrates)
data/                   # crops.csv, soils.csv, rag_store/ (runtime, not committed)
tests/                  # python -m unittest discover -s tests -t .
```
## Local setup

1. Create a virtual environment with Python 3.11.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure the Groq key. For local Streamlit use, create `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "your-key-here"
```

Never commit the real secrets file.

4. Run:

```bash
streamlit run app.py
```

5. Open **Document RAG** in the sidebar, upload one or more text-based PDFs, build the knowledge base, and ask questions.

## Notes

- FAISS is the local vector index. It is rebuilt when the user clicks **Build / Replace Knowledge Base**.
- Sentence Transformers performs the embedding model's tokenization internally.
- The current embedding model is `sentence-transformers/all-MiniLM-L6-v2`.
- The current Groq generation model is `openai/gpt-oss-20b`.
- Scanned/image-only PDFs are not OCR'd in this version. They are reported as unsupported when no selectable text is extracted.
- The application instructs the LLM to answer only from retrieved context and include source/page references.
- On ephemeral cloud deployments, locally generated FAISS files can be lost after a restart/redeploy. A persistent object/database layer should be added for production.
