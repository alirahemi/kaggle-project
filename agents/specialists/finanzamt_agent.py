"""Finanzamt domain specialist — tax assessments and objection deadlines."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool

from agents.specialists.base import create_specialist_agent
from agents.tools import create_mcp_tools
from config.settings import Settings, get_settings

FINANZAMT_TOOLS = (
    "search_knowledge",
    "find_similar_cases",
    "resolve_form",
    "get_official_links",
)


def create_finanzamt_agent(
    settings: Settings | None = None,
    tools: Sequence[BaseTool | Any] | None = None,
) -> LlmAgent:
    """Create the Finanzamt specialist ``LlmAgent``.

    Validates Steuerbescheid patterns, Vorauszahlung amounts, and
    Einspruchsfrist deadlines under AO / EStG.

    Args:
        settings: Optional settings override.
        tools: Optional pre-built tools.

    Returns:
        Configured Finanzamt specialist ``LlmAgent``.
    """
    _ = settings or get_settings()
    default_tools: list[BaseTool | Any] = []
    if tools is None:
        default_tools.extend(create_mcp_tools("rag_mcp", FINANZAMT_TOOLS[:2]))
        default_tools.extend(create_mcp_tools("gov_resources_mcp", FINANZAMT_TOOLS[2:]))

    return create_specialist_agent(
        name="finanzamt_specialist",
        prompt_name="finanzamt",
        description=(
            "Handles Finanzamt letters: Steuerbescheid, Vorauszahlung, "
            "and Einspruchsfrist under AO / EStG."
        ),
        settings=settings,
        tools=tools or default_tools,
    )
