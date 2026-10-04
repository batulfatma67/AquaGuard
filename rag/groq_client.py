from __future__ import annotations

import os

import streamlit as st
from groq import Groq


DEFAULT_MODELS = (
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "llama-3.1-8b-instant",
)

DEFAULT_MODEL = DEFAULT_MODELS[0]


def get_groq_api_key() -> str | None:
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
    model: str | None = None,
) -> str:
    api_key = get_groq_api_key()

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to Streamlit secrets "
            "or configure it as an environment variable."
        )

    client = Groq(api_key=api_key)

    system_prompt = """You are a document-grounded RAG assistant.

Rules:
1. Answer using only the supplied document context.
2. Do not invent unsupported facts.
3. If the context is insufficient, say:
   "I could not find enough information in the uploaded documents to answer that."
4. Keep answers clear and useful.
5. Cite factual claims using source labels provided in the context,
   such as [policy.pdf, p. 4].
6. Only cite sources that support the claims.
"""

    user_prompt = f"""DOCUMENT CONTEXT:
{context}

USER QUESTION:
{question}

Answer using only the document context above.
"""

    preferred_model = (
        model.strip()
        if model and model.strip()
        else os.getenv("GROQ_MODEL", "").strip()
    )

    models = []

    if preferred_model:
        models.append(preferred_model)

    for candidate in DEFAULT_MODELS:
        if candidate not in models:
            models.append(candidate)

    last_error = None

    for candidate in models:
        try:
            completion = client.chat.completions.create(
                model=candidate,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=1200,
            )

            answer = completion.choices[0].message.content

            if not answer or not answer.strip():
                raise RuntimeError("Groq returned an empty response.")

            return answer.strip()

        except Exception as exc:
            last_error = exc

            if getattr(exc, "status_code", None) in (401, 403):
                break

    raise RuntimeError(
        f"Groq could not generate an answer. Last error: {last_error}"
    ) from last_error


def get_grounded_answer(
    question: str,
    context: str,
    model: str | None = None,
) -> str:
    return generate_answer(
        question=question,
        context=context,
        model=model,
    )