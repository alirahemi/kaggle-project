"""Safety gate agent — final output review before user delivery."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool

from agents.callbacks import disclaimer_injector_after_model, pii_guard_before_model
from agents.prompts import load_prompt, load_prompt_metadata
from agents.tools import create_mcp_tools
from config.settings import Settings, get_settings

SAFETY_TOOLS = ("log_interaction",)


def create_safety_agent(
    settings: Settings | None = None,
    tools: Sequence[BaseTool | Any] | None = None,
) -> LlmAgent:
    """Create the safety gate ``LlmAgent``.

    Reviews explainer and action-plan outputs for hallucinations, PII leaks,
    missing disclaimers, and high-risk content before user delivery.

    Args:
        settings: Optional settings override.
        tools: Optional pre-built tools; defaults to audit MCP tool.

    Returns:
        Configured safety gate ``LlmAgent``.
    """
    cfg = settings or get_settings()
    metadata = load_prompt_metadata("safety")
    agent_tools = list(tools) if tools is not None else create_mcp_tools("audit_mcp", SAFETY_TOOLS)

    return LlmAgent(
        name="safety_agent",
        model=cfg.gemini_model_flash,
        description=str(metadata.get("description", "Final safety review before delivery.")),
        instruction=load_prompt("safety"),
        tools=agent_tools,
        before_model_callback=pii_guard_before_model,
        after_model_callback=disclaimer_injector_after_model,
        output_key="safety_review",
    )
