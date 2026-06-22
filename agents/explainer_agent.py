"""Explainer agent — plain-language bilingual explanations for immigrants."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool

from agents.callbacks import disclaimer_injector_after_model
from agents.prompts import load_prompt, load_prompt_metadata
from agents.tools import create_mcp_tools
from config.settings import Settings, get_settings

EXPLAINER_TOOLS = ("get_glossary_term",)


def create_explainer_agent(
    settings: Settings | None = None,
    tools: Sequence[BaseTool | Any] | None = None,
) -> LlmAgent:
    """Create the plain-language explainer ``LlmAgent``.

    Produces summaries citing extracted fields only. Output locale follows
    the ``locale`` session key (``de`` or ``en``).

    Args:
        settings: Optional settings override.
        tools: Optional pre-built tools; defaults to RAG glossary tool.

    Returns:
        Configured explainer ``LlmAgent``.
    """
    cfg = settings or get_settings()
    metadata = load_prompt_metadata("explainer")
    agent_tools = list(tools) if tools is not None else create_mcp_tools("rag_mcp", EXPLAINER_TOOLS)

    return LlmAgent(
        name="explainer_agent",
        model=cfg.gemini_model_pro,
        description=str(metadata.get("description", "Explains letters in plain language.")),
        instruction=load_prompt("explainer"),
        tools=agent_tools,
        after_model_callback=disclaimer_injector_after_model,
        output_key="explanation",
    )
