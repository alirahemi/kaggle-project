"""Disclaimer injector callback — appends legal disclaimer to user-facing output."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from google.adk.models import LlmResponse

DISCLAIMER_PATH = Path(__file__).resolve().parents[2] / "DISCLAIMER.md"


def disclaimer_injector_after_model(
    callback_context: Any,
    llm_response: LlmResponse,
) -> LlmResponse | None:
    """Append the project legal disclaimer to model responses shown to users.

    Registered as ``after_model_callback`` on explainer and safety agents.

    Args:
        callback_context: ADK callback context; reads ``locale`` from state.
        llm_response: Mutable LLM response object.

    Returns:
        Modified ``LlmResponse`` when disclaimer was injected; ``None`` otherwise.
    """
    locale = callback_context.state.get("locale", "en")
    disclaimer = _load_disclaimer(locale)

    text = _extract_response_text(llm_response)
    if not text or disclaimer in text:
        return None

    augmented = f"{text.rstrip()}\n\n---\n\n{disclaimer}"
    _set_response_text(llm_response, augmented)
    callback_context.state["disclaimer_injected"] = True
    return llm_response


def _load_disclaimer(locale: str) -> str:
    if not DISCLAIMER_PATH.exists():
        return _fallback_disclaimer(locale)

    content = DISCLAIMER_PATH.read_text(encoding="utf-8")
    if locale == "de":
        marker = "## Deutsch"
    else:
        marker = "## English"

    if marker not in content:
        return _fallback_disclaimer(locale)

    section = content.split(marker, maxsplit=1)[1]
    next_heading = section.find("\n## ")
    body = section[:next_heading] if next_heading != -1 else section
    return body.strip()


def _fallback_disclaimer(locale: str) -> str:
    if locale == "de":
        return (
            "Dies ist eine KI-generierte Zusammenfassung und ersetzt keine "
            "professionelle Rechtsberatung."
        )
    return (
        "This is an AI-generated summary and is not a substitute for "
        "professional legal advice."
    )


def _extract_response_text(llm_response: LlmResponse) -> str:
    content = getattr(llm_response, "content", None)
    if content is None:
        return ""
    parts = getattr(content, "parts", None) or []
    return "\n".join(getattr(part, "text", "") or "" for part in parts)


def _set_response_text(llm_response: LlmResponse, text: str) -> None:
    content = getattr(llm_response, "content", None)
    if content is None:
        return
    parts = getattr(content, "parts", None)
    if parts:
        for part in parts:
            if hasattr(part, "text"):
                part.text = text
                return
