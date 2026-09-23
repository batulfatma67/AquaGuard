from __future__ import annotations

import os

import streamlit as st
from groq import Groq


DEFAULT_MODEL = "openai/gpt-oss-20b"


def get_groq_api_key() -> str | None:
    """Read the API key from Streamlit secrets first, then environment."""
    try:
        key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        key = None

    if key:
        return str(key).strip()

    key = os.getenv("GROQ_API_KEY")
    return key.strip() if key else None


def generate_answer(
    question: str,
    context: str,
    model: str = DEFAULT_MODEL,
) -> str:
    """Generate a grounded answer from retrieved document context."""
    api_key = get_groq_api_key()

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured. Add it to Streamlit Secrets "
            "or set it as an environment variable."
        )

    client = Groq(api_key=api_key)

    system_prompt = """You are a document-grounded RAG assistant.

Rules:
1. Answer using only the supplied document context.
2. Do not invent facts that are not supported by the context.
3. If the context does not contain enough information, say:
   "I could not find enough information in the uploaded documents to answer that."
4. Keep the answer clear and useful.
5. When making factual claims, cite the supplied source labels in square brackets,
   for example [policy.pdf, p. 4].
6. Do not cite a source that does not support the claim.
"""

    user_prompt = f"""DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

Answer the question using only the document context above.
"""

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=1200,
    )

    answer = completion.choices[0].message.content

    if not answer:
        raise RuntimeError("Groq returned an empty response.")

    return answer.strip()
