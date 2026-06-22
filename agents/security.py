"""Security helpers: PII redaction, disclaimer, safe logging."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("bureaucracy.security")

DISCLAIMER = (
    "This is an AI-generated summary for informational purposes only. "
    "It is not legal advice. Verify all deadlines and obligations against "
    "the original letter and consult a qualified advisor or the issuing authority."
)

_NAME_PATTERN = re.compile(
    r"\b[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+\b"
)
_STREET_PATTERN = re.compile(
    r"\b[A-ZÄÖÜ][a-zäöüß]+(?:straße|str\.|weg|platz|allee)\s+\d+[a-z]?\b",
    re.IGNORECASE,
)
_AKTENZEICHEN_PATTERN = re.compile(r"\b[A-Z]{1,4}-\d{4}-\d{3,6}\b")
_DATE_PATTERN = re.compile(r"\b\d{2}\.\d{2}\.\d{4}\b")

_LOG_DIR = Path("data/logs")
_LOG_DIR.mkdir(parents=True, exist_ok=True)


def redact_pii(text: str) -> tuple[str, bool]:
    """Redact common German PII patterns. Returns (redacted_text, pii_found)."""
    redacted = text
    pii_found = False
    counter = 0

    def _token(label: str, value: str) -> str:
        nonlocal counter, pii_found
        pii_found = True
        counter += 1
        return f"[{label}_{counter}]"

    for pattern, label in (
        (_NAME_PATTERN, "NAME"),
        (_STREET_PATTERN, "ADDRESS"),
        (_AKTENZEICHEN_PATTERN, "CASE_NO"),
    ):
        for match in pattern.finditer(text):
            token = _token(label, match.group())
            redacted = redacted.replace(match.group(), token, 1)

    return redacted, pii_found


def get_disclaimer() -> str:
    return DISCLAIMER


def log_analysis_safe(
    institution: str,
    letter_type: str,
    pii_redacted: bool,
    text_hash: str,
) -> None:
    """Write a redacted audit log entry — never stores letter content."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "institution": institution,
        "letter_type": letter_type,
        "pii_redacted": pii_redacted,
        "text_hash": text_hash,
    }
    log_file = _LOG_DIR / "analysis_audit.jsonl"
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")
    logger.info("Analysis logged (hash=%s…)", text_hash[:12])


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
