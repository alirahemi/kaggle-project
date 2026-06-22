"""Extraction agent — extracts deadlines, documents, amounts, and actions."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from agents.tools.mcp_tools import get_mcp_tools
from config.settings import Settings, get_settings

EXTRACTION_INSTRUCTION = """You extract structured facts from German official letters.

The classifier agent has already run — read its JSON output from the conversation above.

Read the letter and respond with ONLY valid JSON (no markdown fences):
{
  "deadlines": [
    {"date": "YYYY-MM-DD or null", "description": "string", "raw_text": "original German phrase"}
  ],
  "requested_documents": ["list of documents requested"],
  "amounts": [{"value": 0.0, "currency": "EUR", "context": "string"}],
  "required_actions": ["list of actions the recipient must take"],
  "case_number": "string or null",
  "letter_date": "YYYY-MM-DD or null"
}

Rules:
- Extract only facts explicitly stated in the letter.
- Use deadline_calculator tool to resolve dates like 'bis zum 15.07.2025'.
- Do not interpret or advise — facts only.
"""


def create_extraction_agent(settings: Settings | None = None) -> LlmAgent:
    cfg = settings or get_settings()
    return LlmAgent(
        name="extraction_agent",
        model=cfg.gemini_model_pro,
        description="Extracts deadlines, documents, amounts, and required actions.",
        instruction=EXTRACTION_INSTRUCTION,
        tools=get_mcp_tools(),
        output_key="extraction",
    )
