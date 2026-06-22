"""PII redaction tool stubs."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from config.settings import get_settings

_NAME_PATTERN = re.compile(r"\b[A-ZÄÖÜ][a-zäöüß]+ [A-ZÄÖÜ][a-zäöüß]+\b")
_STEUER_ID_PATTERN = re.compile(r"\b\d{11}\b")
_AKTENZEICHEN_PATTERN = re.compile(r"\b[A-Z]{1,4}-\d{2,6}/\d{2,4}\b")


def redact_pii(text: str, preserve_aktenzeichen: bool = False) -> dict[str, Any]:
    """Redact names, addresses, Steuer-ID, and Aktenzeichen patterns."""
    settings = get_settings()
    if not settings.pii_redaction_enabled:
        return {
            "redacted_text": text,
            "redaction_map": {},
            "pii_found": False,
        }

    redaction_map: dict[str, str] = {}
    redacted = text
    pii_found = False
    counters = {"name": 0, "steuer_id": 0, "aktenzeichen": 0}

    def _placeholder(kind: str, value: str) -> str:
        nonlocal pii_found
        pii_found = True
        counters[kind] += 1
        token = f"[{kind.upper()}_{counters[kind]}]"
        redaction_map[token] = hashlib.sha256(value.encode()).hexdigest()[:16]
        return token

    for match in _NAME_PATTERN.finditer(text):
        token = _placeholder("name", match.group())
        redacted = redacted.replace(match.group(), token, 1)

    for match in _STEUER_ID_PATTERN.finditer(text):
        token = _placeholder("steuer_id", match.group())
        redacted = redacted.replace(match.group(), token, 1)

    if not preserve_aktenzeichen:
        for match in _AKTENZEICHEN_PATTERN.finditer(text):
            token = _placeholder("aktenzeichen", match.group())
            redacted = redacted.replace(match.group(), token, 1)

    return {
        "redacted_text": redacted,
        "redaction_map": redaction_map,
        "pii_found": pii_found,
    }
