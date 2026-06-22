"""PII guard callback — scans LLM requests before model invocation."""

from __future__ import annotations

import re
from typing import Any

from google.adk.models import LlmResponse

from config.settings import get_settings

# Common German PII patterns (stub — expand in production).
_PII_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b\d{11}\b"),  # German tax ID (Steuer-ID) length heuristic
    re.compile(r"\bDE\d{20}\b"),  # IBAN
    re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b"),  # Date of birth style
    re.compile(r"\b[A-Z]{1,3}-[A-Z]{1,2}\s?\d{1,4}\b"),  # License plate heuristic
)


def pii_guard_before_model(callback_context: Any, llm_request: Any) -> LlmResponse | None:
    """Block or redact PII detected in outbound LLM request content.

    Registered as ``before_model_callback`` on agents that handle user documents.

    Args:
        callback_context: ADK callback context with session state.
        llm_request: Mutable LLM request object.

    Returns:
        ``LlmResponse`` to short-circuit the model call when PII is detected
        and redaction is enabled; ``None`` to proceed normally.
    """
    settings = get_settings()
    if not settings.pii_redaction_enabled:
        return None

    text = _extract_request_text(llm_request)
    if not text or not _contains_pii(text):
        return None

    redacted = _redact_pii(text)
    _replace_request_text(llm_request, redacted)

    callback_context.state["pii_redacted"] = True
    return None


def _contains_pii(text: str) -> bool:
    return any(pattern.search(text) for pattern in _PII_PATTERNS)


def _redact_pii(text: str) -> str:
    redacted = text
    for pattern in _PII_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _extract_request_text(llm_request: Any) -> str:
    contents = getattr(llm_request, "contents", None) or []
    parts: list[str] = []
    for content in contents:
        for part in getattr(content, "parts", None) or []:
            if text := getattr(part, "text", None):
                parts.append(text)
    return "\n".join(parts)


def _replace_request_text(llm_request: Any, text: str) -> None:
    contents = getattr(llm_request, "contents", None)
    if not contents:
        return
    for content in contents:
        parts = getattr(content, "parts", None)
        if parts:
            for part in parts:
                if hasattr(part, "text"):
                    part.text = text
                    return
