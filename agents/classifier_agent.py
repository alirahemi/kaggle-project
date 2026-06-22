"""Classifier agent — detects German government institution and letter type."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from agents.tools.mcp_tools import get_mcp_tools
from config.settings import Settings, get_settings

CLASSIFIER_INSTRUCTION = """You classify official German government letters.

Read the user's letter and respond with ONLY valid JSON (no markdown fences):
{
  "institution": "Jobcenter" | "Ausländerbehörde" | "Finanzamt" | "Krankenkasse" | "Other",
  "letter_type": "string (e.g. Nachforderung, Bescheid, Termin, Mahnung)",
  "confidence": 0.0-1.0,
  "reasoning": "one sentence"
}

Use the glossary_lookup tool for unfamiliar German terms.
Institution hints:
- Jobcenter: Bürgergeld, ALG II, SGB II, Unterlagen
- Ausländerbehörde: Aufenthaltstitel, AufenthG, Verlängerung
- Finanzamt: Steuerbescheid, Einspruch, ELSTER
- Krankenkasse: Beitrag, Versicherung, SGB V
"""


def create_classifier_agent(settings: Settings | None = None) -> LlmAgent:
    cfg = settings or get_settings()
    return LlmAgent(
        name="classifier_agent",
        model=cfg.gemini_model_flash,
        description="Classifies institution type and letter category.",
        instruction=CLASSIFIER_INSTRUCTION,
        tools=get_mcp_tools(),
        output_key="classification",
    )
