"""Unit tests for MVP MCP tools (no API key required)."""

from mcp_servers.bureaucracy_mcp.tools import deadline_calculator, glossary_lookup


def test_glossary_lookup_found():
    result = glossary_lookup("Bescheid", locale="en")
    assert result["found"] is True
    assert "administrative" in result["definition"].lower()


def test_glossary_lookup_missing():
    result = glossary_lookup("NotARealTermXYZ")
    assert result["found"] is False


def test_deadline_calculator_parses_german_date():
    result = deadline_calculator("Bitte bis zum 15.07.2026 einreichen")
    assert result["parsed"] is True
    assert result["iso_date"] == "2026-07-15"
