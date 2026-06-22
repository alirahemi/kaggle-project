"""Ausländerbehörde domain specialist — residence permits and immigration deadlines."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool

from agents.specialists.base import create_specialist_agent
from agents.tools import create_mcp_tools
from config.settings import Settings, get_settings

AUSLAENDER_TOOLS = (
    "search_knowledge",
    "find_similar_cases",
    "resolve_form",
    "get_official_links",
)


def create_auslaenderbehoerde_agent(
    settings: Settings | None = None,
    tools: Sequence[BaseTool | Any] | None = None,
) -> LlmAgent:
    """Create the Ausländerbehörde specialist ``LlmAgent``.

    Focuses on Aufenthaltstitel, Fristen, Duldung, and appointments.
    Forces escalation when deportation-related language is detected.

    Args:
        settings: Optional settings override.
        tools: Optional pre-built tools.

    Returns:
        Configured Ausländerbehörde specialist ``LlmAgent``.
    """
    _ = settings or get_settings()
    default_tools: list[BaseTool | Any] = []
    if tools is None:
        default_tools.extend(create_mcp_tools("rag_mcp", AUSLAENDER_TOOLS[:2]))
        default_tools.extend(create_mcp_tools("gov_resources_mcp", AUSLAENDER_TOOLS[2:]))

    return create_specialist_agent(
        name="auslaenderbehoerde_specialist",
        prompt_name="auslaenderbehoerde",
        description=(
            "Handles Ausländerbehörde letters: Aufenthaltstitel, Fristen, "
            "Duldung, and Termine under AufenthG / AufenthV."
        ),
        settings=settings,
        tools=tools or default_tools,
    )
