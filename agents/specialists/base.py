"""Base factory for domain specialist ADK agents."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool

from agents.prompts import load_prompt, load_prompt_metadata
from config.settings import Settings, get_settings


def create_specialist_agent(
    *,
    name: str,
    prompt_name: str,
    description: str,
    settings: Settings | None = None,
    tools: Sequence[BaseTool | Any] | None = None,
) -> LlmAgent:
    """Create a domain specialist ``LlmAgent`` with shared configuration.

    Args:
        name: ADK agent name (snake_case).
        prompt_name: YAML prompt stem in ``agents/prompts/``.
        description: Routing description consumed by the orchestrator LLM.
        settings: Optional settings override; defaults to ``get_settings()``.
        tools: MCP-backed or native ADK tools for this specialist.

    Returns:
        Configured ``LlmAgent`` using the Pro model for domain reasoning.
    """
    cfg = settings or get_settings()
    metadata = load_prompt_metadata(prompt_name)

    return LlmAgent(
        name=name,
        model=cfg.gemini_model_pro,
        description=description or str(metadata.get("description", "")),
        instruction=load_prompt(prompt_name),
        tools=list(tools or []),
    )
