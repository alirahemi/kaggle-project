"""ADK FunctionTools wrapping bureaucracy MCP tool implementations."""

from __future__ import annotations

import logging

from google.adk.tools import FunctionTool

from mcp_servers.bureaucracy_mcp.tools import (
    deadline_calculator,
    glossary_lookup,
)

logger = logging.getLogger(__name__)


def glossary_lookup_tool(term: str, locale: str = "en") -> dict:
    """Look up a German bureaucracy term in the glossary."""
    try:
        return glossary_lookup(term=term, locale=locale)
    except Exception as exc:
        logger.warning("glossary_lookup failed: %s", exc)
        return {
            "term": term,
            "definition": "",
            "locale": locale,
            "found": False,
            "error": "Glossary lookup unavailable",
        }


def deadline_calculator_tool(
    deadline_text: str,
    reference_date: str = "",
) -> dict:
    """Parse a German deadline and calculate days remaining."""
    try:
        ref = reference_date or None
        return deadline_calculator(deadline_text=deadline_text, reference_date=ref)
    except Exception as exc:
        logger.warning("deadline_calculator failed: %s", exc)
        return {
            "parsed": False,
            "original": deadline_text,
            "iso_date": None,
            "days_remaining": None,
            "urgency": "unknown",
            "error": "Deadline calculation unavailable",
        }


def get_mcp_tools() -> list[FunctionTool]:
    """Return MCP-backed tools for ADK agents."""
    return [
        FunctionTool(glossary_lookup_tool),
        FunctionTool(deadline_calculator_tool),
    ]
