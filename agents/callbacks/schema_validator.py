"""Schema validation callback — validates agent outputs against JSON schemas."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "config" / "schemas"


def schema_validator_after_agent(callback_context: Any) -> None:
    """Validate the latest agent output against an expected JSON schema.

    Registered as ``after_agent_callback``. Sets ``schema_valid`` and
    ``schema_errors`` keys in session state for downstream safety checks.

    Args:
        callback_context: ADK callback context with session state and events.
    """
    output = callback_context.state.get("last_agent_output")
    schema_name = callback_context.state.get("expected_schema")

    if output is None or not schema_name:
        return

    schema_path = SCHEMAS_DIR / f"{schema_name}.json"
    if not schema_path.exists():
        logger.warning("Schema file missing: %s", schema_path)
        callback_context.state["schema_valid"] = True
        return

    errors = _validate_against_schema(output, schema_path)
    callback_context.state["schema_valid"] = not errors
    callback_context.state["schema_errors"] = errors


def _validate_against_schema(output: Any, schema_path: Path) -> list[str]:
    """Lightweight structural validation stub (full jsonschema in production)."""
    errors: list[str] = []

    with schema_path.open(encoding="utf-8") as handle:
        schema = json.load(handle)

    if not isinstance(output, dict):
        return ["Output must be a JSON object"]

    required = schema.get("required", [])
    for field in required:
        if field not in output:
            errors.append(f"Missing required field: {field}")

    return errors
