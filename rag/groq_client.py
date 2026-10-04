import os

from groq import Groq

# "llama3-70b-8192" was shut down by Groq on 30 Aug 2025, so the old code
# always failed. Models are tried in this order; set the GROQ_MODEL
# environment variable (or Streamlit secret) to force a specific one.
DEFAULT_MODELS = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-20b",
    "llama-3.1-8b-instant",
]

SYSTEM_PROMPT = (
    "You are an expert AI assistant for AquaGuard AI, specializing in agriculture and water management.\n"
    "Follow these rules strictly:\n"
    "1. Answer using only the supplied document context.\n"
    "2. Do not invent facts that are not supported by the context.\n"
    "3. If the context does not contain enough information, say: \"I could not find enough information in the provided documents to answer that.\"\n"
    "4. Keep the answer clear and useful.\n"
    "5. When making factual claims, cite the supplied source labels in square brackets, for example [filename, p. X].\n"
    "6. Do not cite a source that does not support the claim."
)


def _candidate_models():
    custom = os.environ.get("GROQ_MODEL", "").strip()
    return ([custom] if custom else []) + DEFAULT_MODELS


def get_grounded_answer(query, context):
    api_key = os.environ.get("GROQ_API_KEY", "").strip()

    if not api_key:
        return (
            "GROQ_API_KEY is not set. Add it as an environment variable "
            "(Streamlit Cloud: App settings -> Secrets, e.g. "
            "GROQ_API_KEY = \"your_key\") and restart the app."
        )

    user_prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"

    last_error = None

    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        return f"Could not create the Groq client: {e}"

    for model in _candidate_models():
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
            )
            return completion.choices[0].message.content
        except Exception as e:
            last_error = e
            # Wrong/expired key: trying other models will not help.
            if getattr(e, "status_code", None) in (401, 403):
                break

    return (
        f"Error communicating with Groq API: {last_error}. "
        "Please check that GROQ_API_KEY is valid and that the model is still "
        "available (see https://console.groq.com/docs/models)."
    )
