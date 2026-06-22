"""Prompt loading utilities for ADK agents."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

PROMPTS_DIR = Path(__file__).resolve().parent


@lru_cache(maxsize=32)
def load_prompt(name: str) -> str:
    """Load agent instruction text from a YAML prompt file.

    Args:
        name: Prompt filename without extension (e.g. ``orchestrator``).

    Returns:
        The ``instruction`` field from the YAML file.

    Raises:
        FileNotFoundError: If the prompt file does not exist.
        KeyError: If the YAML file lacks an ``instruction`` key.
    """
    path = PROMPTS_DIR / f"{name}.yaml"
    if not path.exists():
        msg = f"Prompt file not found: {path}"
        raise FileNotFoundError(msg)

    with path.open(encoding="utf-8") as handle:
        data: dict[str, Any] = yaml.safe_load(handle) or {}

    instruction = data.get("instruction")
    if not instruction:
        msg = f"Prompt file {path} must contain an 'instruction' key"
        raise KeyError(msg)

    return str(instruction).strip()


def load_prompt_metadata(name: str) -> dict[str, Any]:
    """Load full prompt metadata (name, description, instruction) from YAML."""
    path = PROMPTS_DIR / f"{name}.yaml"
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}
