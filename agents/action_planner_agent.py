"""Action planner agent — produces prioritized actionable checklists."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool

from agents.prompts import load_prompt, load_prompt_metadata
from agents.tools import create_mcp_tools
from config.settings import Settings, get_settings

ACTION_PLANNER_TOOLS = (
    "business_days_until",
    "urgency_score",
    "resolve_form",
    "get_official_links",
)


def create_action_planner_agent(
    settings: Settings | None = None,
    tools: Sequence[BaseTool | Any] | None = None,
) -> LlmAgent:
    """Create the action planner ``LlmAgent``.

    Builds urgent/this-week/later/optional task lists with deadlines and
    official form links.

    Args:
        settings: Optional settings override.
        tools: Optional pre-built tools; defaults to calendar and gov tools.

    Returns:
        Configured action planner ``LlmAgent``.
    """
    cfg = settings or get_settings()
    metadata = load_prompt_metadata("action_planner")
    default_tools: list[BaseTool | Any] = []
    if tools is None:
        default_tools.extend(create_mcp_tools("calendar_mcp", ACTION_PLANNER_TOOLS[:2]))
        default_tools.extend(create_mcp_tools("gov_resources_mcp", ACTION_PLANNER_TOOLS[2:]))
    agent_tools = list(tools) if tools is not None else default_tools

    return LlmAgent(
        name="action_planner_agent",
        model=cfg.gemini_model_pro,
        description=str(metadata.get("description", "Plans prioritized user actions.")),
        instruction=load_prompt("action_planner"),
        tools=agent_tools,
        output_key="action_plan",
    )
