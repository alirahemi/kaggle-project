"""ADK orchestrator — runs classifier → extraction → response_writer in sequence."""

from __future__ import annotations

from google.adk.agents import SequentialAgent

from agents.classifier_agent import create_classifier_agent
from agents.extraction_agent import create_extraction_agent
from agents.response_writer_agent import create_response_writer_agent
from config.settings import Settings, get_settings


def create_orchestrator(settings: Settings | None = None) -> SequentialAgent:
    """Build the MVP multi-agent pipeline orchestrator."""
    cfg = settings or get_settings()
    return SequentialAgent(
        name="bureaucracy_orchestrator",
        description=(
            "Analyzes German government letters: classifies institution, "
            "extracts key facts, then writes explanation and action plan."
        ),
        sub_agents=[
            create_classifier_agent(cfg),
            create_extraction_agent(cfg),
            create_response_writer_agent(cfg),
        ],
    )
