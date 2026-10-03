"""Experimental agent: selects one of a fixed set of tools for a user request.

The model only chooses the tool; calculations come from the engine and answers from RAG.
Report finalisation always requires explicit human confirmation.
"""
from __future__ import annotations

from typing import Callable

INTENTS = ("CALCULATE", "COMPARE", "SEARCH", "REPORT")

ROUTER_PROMPT = """You route requests for the AquaGuard agriculture app.
Reply with ONLY ONE word from this list:
- CALCULATE (water needs, crop demand, irrigation volume for the current farm)
- COMPARE (compare irrigation scenarios or groundwater savings)
- SEARCH (general farming, crop, irrigation, groundwater or remote-sensing knowledge question)
- REPORT (prepare or export a water-account report)
No other words or punctuation."""

_KEYWORDS = {
    "REPORT": ("report", "export", "summary document"),
    "COMPARE": ("compare", "scenario", "what if", "what-if", "saving", "alternative"),
    "CALCULATE": ("calculate", "how much water", "volume", "requirement", "irrigation need", "etc"),
}


def _keyword_intent(message: str) -> str:
    text = message.lower()
    for intent in ("REPORT", "COMPARE", "CALCULATE"):
        if any(k in text for k in _KEYWORDS[intent]):
            return intent
    return "SEARCH"


def route_intent(message: str, api_key: str | None = None) -> str:
    """Choose a tool with Groq when a key is available, else by keywords."""
    if not message.strip():
        raise ValueError("Please enter a request.")
    if not api_key:
        return _keyword_intent(message)

    try:
        from groq import Groq

        response = Groq(api_key=api_key).chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0.0,
            max_tokens=20,
        )
        decision = (response.choices[0].message.content or "").strip().upper()
    except Exception:
        return _keyword_intent(message)

    return next((i for i in INTENTS if i in decision), _keyword_intent(message))


def run_agent(
    message: str,
    tools: dict[str, Callable[[str], str]],
    api_key: str | None = None,
) -> dict:
    """Route and execute; REPORT is returned as a draft that needs confirmation."""
    intent = route_intent(message, api_key)
    if intent not in tools:
        raise ValueError(f"No tool is registered for '{intent}'.")
    output = tools[intent](message)
    return {"intent": intent, "output": output, "needs_confirmation": intent == "REPORT"}
