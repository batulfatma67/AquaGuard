# AquaGuard

AquaGuard AI is a Streamlit prototype for farm-level irrigation water accounting. It estimates crop-water demand and the groundwater share of irrigation, compares what-if irrigation plans, and answers questions from agricultural PDFs. All water figures are modelled estimates, not measurements of actual pumping.

## Pages

- **Overview**: key water-account metrics and quick actions.
- **Farm Profiles**: saved farms with district/tehsil dropdowns; create, view and edit profiles.
- **Farm Intelligence**: crop stage, weather inputs and an illustrative NDVI trend.
- **Water Account**: transparent ETc, net/gross irrigation and groundwater calculation.
- **AquaGuard Decision** and **What-If Scenarios**: compare irrigation plans and flag crop-water stress risk.
- **Reports**: downloadable and saved water-account reports.
- **AI Assistant**: document question answering over the PDF knowledge base.
- **Calculated Q/A**: routes a question to a calculation, scenario comparison, document search or report draft.

## RAG pipeline

PDF upload → PyMuPDF text extraction → overlapping chunks → Sentence Transformers embeddings → FAISS retrieval → Groq answer grounded in the retrieved passages.

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

4. Run (the app is served at <http://localhost:8501>):

```bash
streamlit run app.py
```

5. Open **AI Assistant** in the sidebar, upload one or more text-based PDFs, build the knowledge base, and ask questions.

## Notes

- FAISS is the local vector index. It is rebuilt when the user clicks **Build / Replace Knowledge Base**.
- Sentence Transformers performs the embedding model's tokenization internally.
- The embedding model is `sentence-transformers/all-MiniLM-L6-v2`. It loads only when the knowledge base is built or queried, so the rest of the app starts without it.
- Groq answers try `llama-3.3-70b-versatile`, then `openai/gpt-oss-20b`, then `llama-3.1-8b-instant`. Set `GROQ_MODEL` to prefer a specific model.
- Scanned/image-only PDFs are not OCR'd in this version. They are reported as unsupported when no selectable text is extracted.
- The application instructs the LLM to answer only from retrieved context. Source and page references are not shown in the AI Assistant results.
- On ephemeral cloud deployments, locally generated FAISS files can be lost after a restart/redeploy. A persistent object/database layer should be added for production.
