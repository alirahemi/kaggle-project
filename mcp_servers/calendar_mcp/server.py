"""Calendar MCP server — German date parsing and deadline urgency."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from config.settings import get_settings

SERVER_NAME = "bureaucracy-calendar-mcp"
SERVER_VERSION = "1.0.0"

logger = logging.getLogger(__name__)
settings = get_settings()
server = Server(SERVER_NAME)

_HOLIDAYS_PATH = Path(__file__).parent / "holidays_de.json"

_TOOLS: list[Tool] = [
    Tool(
        name="parse_german_date",
        description="Resolve German date expressions to ISO format.",
        inputSchema={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "German date phrase (e.g. 'bis zum 15. des Folgemonats')",
                },
                "reference_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Reference date for relative expressions (YYYY-MM-DD)",
                },
            },
            "required": ["expression", "reference_date"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "iso_date": {"type": "string", "format": "date"},
                "parsed": {"type": "boolean"},
                "original": {"type": "string"},
            },
            "required": ["iso_date", "parsed", "original"],
        },
    ),
    Tool(
        name="business_days_until",
        description="Count business days until a deadline (Bundesland-aware).",
        inputSchema={
            "type": "object",
            "properties": {
                "target_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Deadline date (YYYY-MM-DD)",
                },
                "bundesland": {
                    "type": "string",
                    "description": "German state code",
                    "default": settings.agent_default_bundesland,
                },
                "from_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Start date (YYYY-MM-DD)",
                },
            },
            "required": ["target_date", "from_date"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "business_days": {"type": "integer"},
                "calendar_days": {"type": "integer"},
                "is_past": {"type": "boolean"},
            },
            "required": ["business_days", "calendar_days", "is_past"],
        },
    ),
    Tool(
        name="urgency_score",
        description="Compute priority score 0–100 for a deadline.",
        inputSchema={
            "type": "object",
            "properties": {
                "deadline": {
                    "type": "string",
                    "format": "date",
                    "description": "Deadline date (YYYY-MM-DD)",
                },
                "consequence_severity": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "description": "Impact if deadline is missed",
                },
                "bundesland": {
                    "type": "string",
                    "description": "German state code",
                    "default": settings.agent_default_bundesland,
                },
            },
            "required": ["deadline", "consequence_severity"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "score": {"type": "integer", "minimum": 0, "maximum": 100},
                "tier": {"type": "string", "enum": ["urgent", "soon", "normal", "low"]},
            },
            "required": ["score", "tier"],
        },
    ),
]


def _load_holidays(bundesland: str, year: int) -> set[date]:
    if not _HOLIDAYS_PATH.exists():
        return set()
    data = json.loads(_HOLIDAYS_PATH.read_text(encoding="utf-8"))
    bl = data.get("bundeslaender", {}).get(bundesland, {})
    entries = bl.get("holidays", {}).get(str(year), [])
    return {date.fromisoformat(item["date"]) for item in entries}


def _parse_german_date(expression: str, reference_date: str) -> dict[str, Any]:
    ref = date.fromisoformat(reference_date)
    original = expression

    folgemonat_match = re.search(
        r"(\d{1,2})\.\s*des\s+Folgemonats", expression, re.IGNORECASE
    )
    if folgemonat_match:
        day = int(folgemonat_match.group(1))
        if ref.month == 12:
            target = date(ref.year + 1, 1, day)
        else:
            target = date(ref.year, ref.month + 1, day)
        return {"iso_date": target.isoformat(), "parsed": True, "original": original}

    iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", expression)
    if iso_match:
        return {
            "iso_date": iso_match.group(1),
            "parsed": True,
            "original": original,
        }

    de_match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", expression)
    if de_match:
        day, month, year = map(int, de_match.groups())
        return {
            "iso_date": date(year, month, day).isoformat(),
            "parsed": True,
            "original": original,
        }

    return {
        "iso_date": ref.isoformat(),
        "parsed": False,
        "original": original,
    }


def _is_business_day(d: date, holidays: set[date]) -> bool:
    return d.weekday() < 5 and d not in holidays


def _business_days_until(
    target_date: str, bundesland: str, from_date: str
) -> dict[str, Any]:
    target = date.fromisoformat(target_date)
    start = date.fromisoformat(from_date)
    calendar_days = (target - start).days
    is_past = calendar_days < 0

    holidays = _load_holidays(bundesland, start.year) | _load_holidays(
        bundesland, target.year
    )
    business_days = 0
    current = start
    step = 1 if target >= start else -1
    while current != target:
        current += timedelta(days=step)
        if _is_business_day(current, holidays):
            business_days += step

    return {
        "business_days": business_days,
        "calendar_days": calendar_days,
        "is_past": is_past,
    }


def _urgency_score(
    deadline: str, consequence_severity: str, bundesland: str
) -> dict[str, Any]:
    today = date.today()
    target = date.fromisoformat(deadline)
    days_left = (target - today).days

    severity_weight = {"high": 40, "medium": 25, "low": 10}[consequence_severity]
    if days_left <= 0:
        time_score = 100
    elif days_left <= 3:
        time_score = 90
    elif days_left <= 7:
        time_score = 75
    elif days_left <= 14:
        time_score = 55
    elif days_left <= 30:
        time_score = 35
    else:
        time_score = 15

    score = min(100, time_score + severity_weight // 2)
    if score >= 80:
        tier = "urgent"
    elif score >= 60:
        tier = "soon"
    elif score >= 35:
        tier = "normal"
    else:
        tier = "low"

    _ = bundesland  # reserved for holiday-aware urgency in production
    return {"score": score, "tier": tier}


_TOOL_HANDLERS: dict[str, Any] = {
    "parse_german_date": lambda args: _parse_german_date(
        args["expression"], args["reference_date"]
    ),
    "business_days_until": lambda args: _business_days_until(
        args["target_date"],
        args.get("bundesland", settings.agent_default_bundesland),
        args["from_date"],
    ),
    "urgency_score": lambda args: _urgency_score(
        args["deadline"],
        args["consequence_severity"],
        args.get("bundesland", settings.agent_default_bundesland),
    ),
}


@server.list_tools()
async def list_tools() -> list[Tool]:
    return _TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    args = arguments or {}
    handler = _TOOL_HANDLERS.get(name)
    if handler is None:
        raise ValueError(f"MCP_TOOL_NOT_FOUND: unknown tool {name!r}")

    try:
        result = handler(args)
    except (KeyError, ValueError) as exc:
        raise ValueError(f"MCP_VALIDATION_ERROR: {exc}") from exc

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


async def run() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=SERVER_NAME,
                server_version=SERVER_VERSION,
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    logging.basicConfig(level=settings.log_level)
    asyncio.run(run())
