"""End-to-end letter analysis pipeline for Streamlit and CLI."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agents.demo_fallback import build_demo_analysis
from agents.errors import (
    EmptyInputError,
    GeminiApiError,
    MissingApiKeyError,
    PipelineError,
    QuotaExceededError,
)
from agents.root_orchestrator import create_orchestrator
from agents.security import get_disclaimer, hash_text, log_analysis_safe, redact_pii
from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

APP_NAME = "german-bureaucracy-agent"

_GEMINI_ERROR_HINTS = (
    "api key",
    "api_key",
    "invalid",
    "permission",
    "quota",
    "rate limit",
    "429",
    "403",
    "401",
    "resource exhausted",
    "unauthenticated",
)


def _ensure_api_key(settings: Settings) -> None:
    key = settings.google_api_key or os.environ.get("GOOGLE_API_KEY", "")
    if not key or key.startswith("your-"):
        raise MissingApiKeyError(
            "GOOGLE_API_KEY is not set. Copy .env.example to .env and add your key "
            "from https://aistudio.google.com/apikey"
        )
    os.environ["GOOGLE_API_KEY"] = key


def _parse_json_from_text(text: str) -> dict[str, Any]:
    """Extract JSON object from agent response text."""
    if not text or not text.strip():
        return {}
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {"raw": text}


def _as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        return [value]
    return []


def _normalize_extraction(data: dict[str, Any]) -> dict[str, Any]:
    """Coerce extraction output into a stable shape."""
    if not isinstance(data, dict) or data.get("raw"):
        return {
            "deadlines": [],
            "requested_documents": [],
            "amounts": [],
            "required_actions": [],
            "case_number": None,
            "letter_date": None,
            "_parse_warning": "Extraction returned unstructured text.",
        }

    deadlines = []
    for item in _as_list(data.get("deadlines")):
        if isinstance(item, dict):
            deadlines.append({
                "date": item.get("date"),
                "description": item.get("description", ""),
                "raw_text": item.get("raw_text", ""),
            })
        elif isinstance(item, str):
            deadlines.append({"date": None, "description": item, "raw_text": item})

    amounts = []
    for item in _as_list(data.get("amounts")):
        if isinstance(item, dict):
            amounts.append(item)

    return {
        "deadlines": deadlines,
        "requested_documents": [str(d) for d in _as_list(data.get("requested_documents"))],
        "amounts": amounts,
        "required_actions": [str(a) for a in _as_list(data.get("required_actions"))],
        "case_number": data.get("case_number"),
        "letter_date": data.get("letter_date"),
    }


def _normalize_analysis(data: dict[str, Any]) -> dict[str, Any]:
    """Coerce response-writer output into a stable shape."""
    if not isinstance(data, dict) or data.get("raw"):
        return {
            "explanation_en": data.get("raw", "") if isinstance(data, dict) else "",
            "action_checklist": [],
            "reply_draft_de": "",
            "key_terms_explained": [],
            "_parse_warning": "Analysis returned unstructured text.",
        }

    checklist = []
    for item in _as_list(data.get("action_checklist")):
        if isinstance(item, dict):
            checklist.append({
                "priority": item.get("priority", "later"),
                "action": item.get("action", ""),
                "deadline": item.get("deadline"),
            })
        elif isinstance(item, str):
            checklist.append({"priority": "later", "action": item, "deadline": None})

    terms = []
    for item in _as_list(data.get("key_terms_explained")):
        if isinstance(item, dict):
            terms.append({
                "term": item.get("term", ""),
                "meaning_en": item.get("meaning_en", item.get("definition", "")),
            })

    return {
        "explanation_en": str(data.get("explanation_en", "")),
        "action_checklist": checklist,
        "reply_draft_de": str(data.get("reply_draft_de", "")),
        "key_terms_explained": terms,
    }


def _normalize_classification(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("raw"):
        return {
            "institution": "Other",
            "letter_type": "Unknown",
            "confidence": None,
            "reasoning": "",
            "_parse_warning": "Classification returned unstructured text.",
        }
    confidence = data.get("confidence")
    try:
        confidence = float(confidence) if confidence is not None else None
    except (TypeError, ValueError):
        confidence = None
    return {
        "institution": data.get("institution") or "Other",
        "letter_type": data.get("letter_type") or "Unknown",
        "confidence": confidence,
        "reasoning": str(data.get("reasoning", "")),
    }


def _extract_agent_outputs(
    session_state: dict[str, Any],
    events_text: list[str],
) -> dict[str, Any]:
    """Merge session state keys and parse JSON outputs."""
    result: dict[str, Any] = {}

    for key in ("classification", "extraction", "analysis"):
        value = session_state.get(key)
        if isinstance(value, str):
            result[key] = _parse_json_from_text(value)
        elif isinstance(value, dict):
            result[key] = value

    if not result.get("analysis") and events_text:
        result["analysis"] = _parse_json_from_text(events_text[-1])

    return result


def _is_quota_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    return any(
        hint in message
        for hint in ("429", "resource exhausted", "quota", "rate limit")
    )


def _is_gemini_error(exc: BaseException) -> bool:
    message = str(exc).lower()
    return any(hint in message for hint in _GEMINI_ERROR_HINTS)


def _run_coro_sync(coro: Any) -> Any:
    """Run async pipeline safely from Streamlit's sync context."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


async def _run_pipeline_async(letter_text: str, settings: Settings) -> dict[str, Any]:
    _ensure_api_key(settings)

    redacted_text, pii_found = redact_pii(letter_text.strip())
    text_hash = hash_text(letter_text)

    session_service = InMemorySessionService()
    orchestrator = create_orchestrator(settings)

    runner = Runner(
        app_name=APP_NAME,
        agent=orchestrator,
        session_service=session_service,
    )

    user_id = "streamlit-user"
    session_id = str(uuid.uuid4())

    await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=f"Analyze this German official letter:\n\n{redacted_text}"
            )
        ],
    )

    events_text: list[str] = []
    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=message,
        ):
            if hasattr(event, "content") and event.content:
                for part in event.content.parts or []:
                    if hasattr(part, "text") and part.text:
                        events_text.append(part.text)
    except Exception as exc:
        logger.exception("ADK pipeline failed")
        if _is_quota_error(exc):
            raise QuotaExceededError(
                "Gemini free-tier quota exceeded (429 RESOURCE_EXHAUSTED). "
                "Wait a minute and try again, or enable DEMO_MODE=true for recording."
            ) from exc
        if _is_gemini_error(exc):
            raise GeminiApiError(
                f"Gemini API error: {exc}. Check your API key, quota, and network."
            ) from exc
        raise PipelineError(f"Analysis pipeline failed: {exc}") from exc

    session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=user_id,
        session_id=session_id,
    )
    state = dict(session.state) if session else {}
    parsed = _extract_agent_outputs(state, events_text)

    classification = _normalize_classification(parsed.get("classification", {}))
    extraction = _normalize_extraction(parsed.get("extraction", {}))
    analysis = _normalize_analysis(parsed.get("analysis", {}))

    warnings: list[str] = []
    for block in (classification, extraction, analysis):
        warning = block.pop("_parse_warning", None)
        if warning:
            warnings.append(warning)

    if not analysis.get("explanation_en") and not events_text:
        warnings.append("No model response received — try again.")

    institution = classification["institution"]
    letter_type = classification["letter_type"]

    try:
        log_analysis_safe(
            institution=institution,
            letter_type=letter_type,
            pii_redacted=pii_found,
            text_hash=text_hash,
        )
    except Exception as exc:
        logger.warning("Audit log failed: %s", exc)

    return {
        "institution": institution,
        "letter_type": letter_type,
        "confidence": classification["confidence"],
        "classification_reasoning": classification["reasoning"],
        "extraction": extraction,
        "explanation_en": analysis["explanation_en"],
        "action_checklist": analysis["action_checklist"],
        "reply_draft_de": analysis["reply_draft_de"],
        "key_terms_explained": analysis["key_terms_explained"],
        "disclaimer": get_disclaimer(),
        "pii_redacted": pii_found,
        "redacted_preview": redacted_text[:500],
        "warnings": warnings,
    }


def analyze_letter(letter_text: str, settings: Settings | None = None) -> dict[str, Any]:
    """Synchronous entry point for Streamlit."""
    if not letter_text or not letter_text.strip():
        raise EmptyInputError("Please paste or upload a letter before analyzing.")
    cfg = settings or get_settings()

    if cfg.demo_mode:
        return build_demo_analysis(letter_text, reason="demo_mode")

    try:
        return _run_coro_sync(_run_pipeline_async(letter_text, cfg))
    except QuotaExceededError:
        if cfg.demo_fallback_on_quota:
            return build_demo_analysis(letter_text, reason="quota_exceeded")
        raise
    except GeminiApiError as exc:
        if cfg.demo_fallback_on_quota and _is_quota_error(exc):
            return build_demo_analysis(letter_text, reason="quota_exceeded")
        raise
