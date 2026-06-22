"""Intake agent — normalizes uploaded documents into redacted machine-readable text."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.tools import BaseTool

from agents.callbacks import pii_guard_before_model
from agents.prompts import load_prompt, load_prompt_metadata
from agents.tools import create_mcp_tools
from config.settings import Settings, get_settings

INTAKE_TOOLS = (
    "parse_document",
    "ocr_document",
    "redact_pii",
    "store_document",
)


def create_intake_agent(
    settings: Settings | None = None,
    tools: Sequence[BaseTool | Any] | None = None,
) -> LlmAgent:
    """Create the document intake ``LlmAgent``.

    Parses PDFs, applies OCR when needed, redacts PII, and stores documents
    via ``document_mcp`` tools.

    Args:
        settings: Optional settings override.
        tools: Optional pre-built tools; defaults to MCP document tools.

    Returns:
        Configured intake ``LlmAgent``.
    """
    cfg = settings or get_settings()
    metadata = load_prompt_metadata("intake")
    agent_tools = list(tools) if tools is not None else create_mcp_tools("document_mcp", INTAKE_TOOLS)

    return LlmAgent(
        name="intake_agent",
        model=cfg.gemini_model_flash,
        description=str(metadata.get("description", "Normalizes uploaded government letters.")),
        instruction=load_prompt("intake"),
        tools=agent_tools,
        before_model_callback=pii_guard_before_model,
        output_key="intake_result",
    )
