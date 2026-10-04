import streamlit as st

from rag.pipeline import ask_rag, build_knowledge_base, get_store_info


def render() -> None:
    st.title("📚 Document RAG")
    st.caption(
        "Upload PDF documents, build a local FAISS knowledge base, "
        "and ask questions using retrieval-augmented generation."
    )

    st.html(
        """
        <div class="callout">
            <b>How it works</b>
            <p style="margin:8px 0 0;">
                PDF extraction → text cleaning → overlapping chunks →
                local sentence-transformer embeddings → FAISS retrieval →
                Groq LLM answer with source/page references.
            </p>
        </div>
        """
    )

    left, right = st.columns([1.15, 1])

    with left:
        st.subheader("1. Build Knowledge Base")
        uploaded_files = st.file_uploader(
            "Upload one or more PDF documents",
            type=["pdf"],
            accept_multiple_files=True,
            help="Text-based PDFs are supported. Scanned/image-only PDFs require OCR.",
        )
        chunk_size = st.slider("Chunk size (characters)", 400, 1800, 900, 100)
        chunk_overlap = st.slider("Chunk overlap (characters)", 50, 400, 150, 25)
        top_k = st.slider("Retrieved chunks per question", 2, 8, 4)

        if st.button("🔨 Build / Replace Knowledge Base", type="primary", width="stretch"):
            if not uploaded_files:
                st.warning("Please upload at least one PDF.")
            elif chunk_overlap >= chunk_size:
                st.error("Chunk overlap must be smaller than chunk size.")
            else:
                with st.spinner("Extracting PDFs, chunking, embedding and building FAISS..."):
                    try:
                        info = build_knowledge_base(
                            uploaded_files, chunk_size=chunk_size, chunk_overlap=chunk_overlap
                        )
                        st.session_state["rag_messages"] = []
                        st.success(
                            f"Knowledge base ready: {info['documents']} document(s), "
                            f"{info['chunks']} chunk(s)."
                        )
                        for item in info.get("skipped", []):
                            st.warning(f"Skipped: {item}")
                    except Exception as exc:
                        st.error(f"Knowledge-base build failed: {exc}")

    with right:
        st.subheader("Knowledge Base Status")
        try:
            info = get_store_info()
        except Exception:
            info = None

        if info:
            st.metric("Documents", info.get("documents", 0))
            st.metric("Indexed chunks", info.get("chunks", 0))
            st.caption(f"Embedding model: {info.get('embedding_model', 'N/A')}")
            st.caption(f"Vector dimension: {info.get('dimension', 'N/A')}")
        else:
            st.info("No FAISS knowledge base found yet. Upload PDFs and build one.")

        st.markdown("### API configuration")
        st.caption(
            "The Groq API key is read from GROQ_API_KEY (Streamlit secrets or environment). "
            "Never commit it to GitHub."
        )

    st.divider()
    st.subheader("2. Ask Your Documents")

    for message in st.session_state["rag_messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Ask a question about the uploaded documents...")
    if not question:
        return

    st.session_state["rag_messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving relevant passages and generating answer..."):
            try:
                answer, sources = ask_rag(question, top_k=top_k)
                st.markdown(answer)
                if sources:
                    st.session_state["rag_evidence"] = sources
                    with st.expander("📌 Retrieved sources"):
                        for s in sources:
                            st.markdown(
                                f"- **{s['source']}**, page {s['page']} "
                                f"(similarity: {s['score']:.3f})"
                            )
                st.session_state["rag_messages"].append({"role": "assistant", "content": answer})
            except Exception as exc:
                msg = f"RAG query failed: {exc}"
                st.error(msg)
                st.session_state["rag_messages"].append({"role": "assistant", "content": msg})
