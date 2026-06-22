"""Generic government specialist — fallback for Ordnungsamt, Bürgeramt, and others."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool

from agents.specialists.base import create_specialist_agent
from agents.tools import create_mcp_tools
from config.settings import Settings, get_settings

GENERIC_GOV_TOOLS = (
    "search_knowledge",
    "find_similar_cases",
)


def create_generic_gov_agent(
    settings: Settings | None = None,
    tools: Sequence[BaseTool | Any] | None = None,
) -> LlmAgent:
    """Create the generic government specialist ``LlmAgent``.

    Fallback handler for authorities not covered by dedicated specialists
    (Ordnungsamt, Bürgeramt, Sonstige Behörden).

    Args:
        settings: Optional settings override.
        tools: Optional pre-built tools.

    Returns:
        Configured generic government specialist ``LlmAgent``.
    """
    _ = settings or get_settings()

    return create_specialist_agent(
        name="generic_gov_specialist",
        prompt_name="generic_gov",
        description=(
            "Fallback specialist for other government authorities: Ordnungsamt, "
            "Bürgeramt, and unclassified Behörden."
        ),
        settings=settings,
        tools=tools or create_mcp_tools("rag_mcp", GENERIC_GOV_TOOLS),
    )
