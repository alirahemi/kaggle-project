"""Core MCP tool implementations — shared by MCP server and ADK agents."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

_GLOSSARY_PATH = Path(__file__).resolve().parents[2] / "knowledge" / "glossary" / "terms.json"


def _load_glossary() -> list[dict]:
    if not _GLOSSARY_PATH.exists():
        return []
    with _GLOSSARY_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return data.get("terms", [])


def glossary_lookup(term: str, locale: str = "en") -> dict:
    """Look up a German bureaucracy term in the curated glossary."""
    try:
        needle = term.strip().lower()
        for entry in _load_glossary():
            if entry.get("term", "").lower() == needle:
                key = "definition_en" if locale == "en" else "definition_de"
                return {
                    "term": entry["term"],
                    "definition": entry.get(key, entry.get("definition_en", "")),
                    "locale": locale,
                    "found": True,
                }
        return {"term": term, "definition": "", "locale": locale, "found": False}
    except Exception:
        return {"term": term, "definition": "", "locale": locale, "found": False, "error": "lookup_failed"}


def deadline_calculator(
    deadline_text: str,
    reference_date: str | None = None,
) -> dict:
    """Parse a German deadline and compute days remaining."""
    ref = date.today()
    if reference_date:
        ref = datetime.strptime(reference_date, "%Y-%m-%d").date()

    iso_date: str | None = None
    match = re.search(r"\b(\d{2})\.(\d{2})\.(\d{4})\b", deadline_text)
    if match:
        d, m, y = match.groups()
        iso_date = f"{y}-{m}-{d}"
        deadline = date(int(y), int(m), int(d))
    else:
        return {
            "parsed": False,
            "original": deadline_text,
            "iso_date": None,
            "days_remaining": None,
            "urgency": "unknown",
        }

    days_remaining = (deadline - ref).days
    if days_remaining < 0:
        urgency = "overdue"
    elif days_remaining <= 7:
        urgency = "urgent"
    elif days_remaining <= 14:
        urgency = "soon"
    else:
        urgency = "normal"

    return {
        "parsed": True,
        "original": deadline_text,
        "iso_date": iso_date,
        "days_remaining": days_remaining,
        "urgency": urgency,
    }


def business_days_until(target_iso: str, from_iso: str | None = None) -> dict:
    """Count business days until a deadline (Mon–Fri, no holidays)."""
    start = date.today() if not from_iso else datetime.strptime(from_iso, "%Y-%m-%d").date()
    end = datetime.strptime(target_iso, "%Y-%m-%d").date()
    if end < start:
        return {"business_days": 0, "is_past": True}

    count = 0
    current = start
    while current < end:
        current += timedelta(days=1)
        if current.weekday() < 5:
            count += 1
    return {"business_days": count, "is_past": False}
