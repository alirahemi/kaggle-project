"""Krankenkasse domain specialist — health insurance contributions and notices."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool

from agents.specialists.base import create_specialist_agent
from agents.tools import create_mcp_tools
from config.settings import Settings, get_settings

KRANKENKASSE_TOOLS = (
    "search_knowledge",
    "find_similar_cases",
    "resolve_form",
    "get_official_links",
)


def create_krankenkasse_agent(
    settings: Settings | None = None,
    tools: Sequence[BaseTool | Any] | None = None,
) -> LlmAgent:
    """Create the Krankenkasse specialist ``LlmAgent``.

    Handles Beiträge, Familienversicherung, and Nachweise under SGB V / SGB XI.

    Args:
        settings: Optional settings override.
        tools: Optional pre-built tools.

    Returns:
        Configured Krankenkasse specialist ``LlmAgent``.
    """
    _ = settings or get_settings()
    default_tools: list[BaseTool | Any] = []
    if tools is None:
        default_tools.extend(create_mcp_tools("rag_mcp", KRANKENKASSE_TOOLS[:2]))
        default_tools.extend(create_mcp_tools("gov_resources_mcp", KRANKENKASSE_TOOLS[2:]))

    return create_specialist_agent(
        name="krankenkasse_specialist",
        prompt_name="krankenkasse",
        description=(
            "Handles Krankenkasse letters: Beiträge, Familienversicherung, "
            "and Nachweise under SGB V / SGB XI."
        ),
        settings=settings,
        tools=tools or default_tools,
    )
