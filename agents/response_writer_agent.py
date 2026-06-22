"""Response writer agent — explanation, checklist, and German reply draft."""

from __future__ import annotations

from google.adk.agents import LlmAgent

from agents.tools.mcp_tools import get_mcp_tools
from config.settings import Settings, get_settings

RESPONSE_WRITER_INSTRUCTION = """You help immigrants understand German official letters.

The classifier and extraction agents have already run — read their JSON outputs from the conversation above.

Respond with ONLY valid JSON (no markdown fences):
{
  "explanation_en": "Clear plain-English summary (3-5 sentences). Explain what the letter means and what is at stake.",
  "action_checklist": [
    {"priority": "urgent|soon|later", "action": "string", "deadline": "YYYY-MM-DD or null"}
  ],
  "reply_draft_de": "A polite formal German reply letter the user could send. Use [NAME] and [ADDRESS] placeholders. 4-8 sentences.",
  "key_terms_explained": [
    {"term": "German term", "meaning_en": "simple English explanation"}
  ]
}

Rules:
- Base everything on the extraction data — do not invent deadlines.
- Use glossary_lookup for key German terms.
- Sort checklist by urgency (deadlines first).
- The German reply should be respectful and professional (Sehr geehrte Damen und Herren...).
- This is NOT legal advice — be factual and cautious.
"""


def create_response_writer_agent(settings: Settings | None = None) -> LlmAgent:
    cfg = settings or get_settings()
    return LlmAgent(
        name="response_writer_agent",
        model=cfg.gemini_model_pro,
        description="Writes English explanation, action checklist, and German reply draft.",
        instruction=RESPONSE_WRITER_INSTRUCTION,
        tools=get_mcp_tools(),
        output_key="analysis",
    )
