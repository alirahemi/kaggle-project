"""Jobcenter domain specialist — ALG II, Bürgergeld, Mitwirkungspflicht."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool

from agents.specialists.base import create_specialist_agent
from agents.tools import create_mcp_tools
from config.settings import Settings, get_settings

JOB_CENTER_TOOLS = (
    "search_knowledge",
    "find_similar_cases",
    "resolve_form",
    "get_official_links",
)


def create_jobcenter_agent(
    settings: Settings | None = None,
    tools: Sequence[BaseTool | Any] | None = None,
) -> LlmAgent:
    """Create the Jobcenter specialist ``LlmAgent``.

    Validates extractions against SGB II / SGB XII patterns and flags
    anomalies such as unusual penalty amounts or malformed Aktenzeichen.

    Args:
        settings: Optional settings override.
        tools: Optional pre-built tools.

    Returns:
        Configured Jobcenter specialist ``LlmAgent``.
    """
    _ = settings or get_settings()
    default_tools: list[BaseTool | Any] = []
    if tools is None:
        default_tools.extend(create_mcp_tools("rag_mcp", JOB_CENTER_TOOLS[:2]))
        default_tools.extend(create_mcp_tools("gov_resources_mcp", JOB_CENTER_TOOLS[2:]))

    return create_specialist_agent(
        name="jobcenter_specialist",
        prompt_name="jobcenter",
        description=(
            "Handles Jobcenter letters: ALG II, Bürgergeld, Mitwirkungspflicht, "
            "and Nachweise under SGB II / SGB XII."
        ),
        settings=settings,
        tools=tools or default_tools,
    )
