"""Audit MCP server — interaction logging and GDPR data operations."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from config.settings import get_settings

SERVER_NAME = "bureaucracy-audit-mcp"
SERVER_VERSION = "1.0.0"

logger = logging.getLogger(__name__)
settings = get_settings()
server = Server(SERVER_NAME)

_AUDIT_DIR = Path(settings.storage_local_path) / "audit"
_SESSIONS_FILE = _AUDIT_DIR / "sessions.json"
_USER_DATA_FILE = _AUDIT_DIR / "user_data.json"


def _ensure_audit_dir() -> Path:
    _AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    return _AUDIT_DIR


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: dict[str, Any]) -> None:
    _ensure_audit_dir()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


TOOLS: list[Tool] = [
    Tool(
        name="log_interaction",
        description="Log an agent step without PII.",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session UUID"},
                "agent_name": {"type": "string", "description": "Agent identifier"},
                "tool_name": {
                    "type": ["string", "null"],
                    "description": "MCP tool invoked, if any",
                },
                "duration_ms": {
                    "type": "integer",
                    "description": "Execution duration in milliseconds",
                },
                "outcome": {
                    "type": "string",
                    "enum": ["success", "error"],
                    "description": "Step outcome",
                },
            },
            "required": ["session_id", "agent_name", "duration_ms", "outcome"],
        },
        outputSchema={
            "type": "object",
            "properties": {"event_id": {"type": "string"}},
            "required": ["event_id"],
        },
    ),
    Tool(
        name="get_session_summary",
        description="Retrieve session audit trail.",
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Session UUID"},
            },
            "required": ["session_id"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "events": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "agent_name": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"},
                            "outcome": {"type": "string"},
                        },
                        "required": ["agent_name", "timestamp", "outcome"],
                    },
                }
            },
            "required": ["events"],
        },
    ),
    Tool(
        name="export_user_data",
        description="GDPR Art. 15 data export.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User UUID"},
            },
            "required": ["user_id"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "export_url": {"type": "string"},
                "expires_at": {"type": "string", "format": "date-time"},
            },
            "required": ["export_url", "expires_at"],
        },
    ),
    Tool(
        name="delete_user_data",
        description="GDPR Art. 17 erasure.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User UUID"},
                "confirm": {
                    "type": "boolean",
                    "description": "Must be true to execute deletion",
                },
            },
            "required": ["user_id", "confirm"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "deleted": {"type": "boolean"},
                "documents_removed": {"type": "integer"},
                "sessions_removed": {"type": "integer"},
            },
            "required": ["deleted", "documents_removed", "sessions_removed"],
        },
    ),
]


def _log_interaction(
    session_id: str,
    agent_name: str,
    duration_ms: int,
    outcome: str,
    tool_name: str | None = None,
) -> dict[str, Any]:
    event_id = str(uuid.uuid4())
    sessions = _load_json(_SESSIONS_FILE)
    events = sessions.setdefault(session_id, [])
    events.append(
        {
            "event_id": event_id,
            "agent_name": agent_name,
            "tool_name": tool_name,
            "duration_ms": duration_ms,
            "outcome": outcome,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )
    _save_json(_SESSIONS_FILE, sessions)
    return {"event_id": event_id}


def _get_session_summary(session_id: str) -> dict[str, Any]:
    sessions = _load_json(_SESSIONS_FILE)
    raw_events = sessions.get(session_id, [])
    events = [
        {
            "agent_name": e["agent_name"],
            "timestamp": e["timestamp"],
            "outcome": e["outcome"],
        }
        for e in raw_events
    ]
    return {"events": events}


def _export_user_data(user_id: str) -> dict[str, Any]:
    expires_at = (datetime.now(UTC) + timedelta(hours=24)).isoformat()
    export_id = str(uuid.uuid4())
    export_url = f"file://{_AUDIT_DIR}/exports/{user_id}/{export_id}.json"

    user_data = _load_json(_USER_DATA_FILE)
    user_data.setdefault(user_id, {})["last_export"] = {
        "export_id": export_id,
        "export_url": export_url,
        "expires_at": expires_at,
    }
    _save_json(_USER_DATA_FILE, user_data)

    export_dir = _AUDIT_DIR / "exports" / user_id
    export_dir.mkdir(parents=True, exist_ok=True)
    export_path = export_dir / f"{export_id}.json"
    export_path.write_text(
        json.dumps(
            {
                "user_id": user_id,
                "exported_at": datetime.now(UTC).isoformat(),
                "sessions": [
                    sid
                    for sid, events in _load_json(_SESSIONS_FILE).items()
                    if any(e.get("agent_name") for e in events)
                ],
                "note": "[stub] Production export will aggregate all user-held data.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {"export_url": export_url, "expires_at": expires_at}


def _delete_user_data(user_id: str, confirm: bool) -> dict[str, Any]:
    if not confirm:
        return {"deleted": False, "documents_removed": 0, "sessions_removed": 0}

    user_data = _load_json(_USER_DATA_FILE)
    user_data.pop(user_id, None)
    _save_json(_USER_DATA_FILE, user_data)

    export_dir = _AUDIT_DIR / "exports" / user_id
    documents_removed = 0
    if export_dir.exists():
        documents_removed = len(list(export_dir.glob("*.json")))
        for path in export_dir.glob("*.json"):
            path.unlink()

    sessions = _load_json(_SESSIONS_FILE)
    sessions_removed = len(sessions)
    _save_json(_SESSIONS_FILE, {})

    doc_index_path = Path(settings.storage_local_path) / "document_index.json"
    if doc_index_path.exists():
        doc_index = json.loads(doc_index_path.read_text(encoding="utf-8"))
        to_remove = [k for k, v in doc_index.items() if v.get("user_id") == user_id]
        for key in to_remove:
            doc_index.pop(key)
            documents_removed += 1
        doc_index_path.write_text(json.dumps(doc_index, indent=2), encoding="utf-8")

    return {
        "deleted": True,
        "documents_removed": documents_removed,
        "sessions_removed": sessions_removed,
    }


_TOOL_HANDLERS: dict[str, Any] = {
    "log_interaction": lambda args: _log_interaction(
        args["session_id"],
        args["agent_name"],
        args["duration_ms"],
        args["outcome"],
        args.get("tool_name"),
    ),
    "get_session_summary": lambda args: _get_session_summary(args["session_id"]),
    "export_user_data": lambda args: _export_user_data(args["user_id"]),
    "delete_user_data": lambda args: _delete_user_data(args["user_id"], args["confirm"]),
}


@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    args = arguments or {}
    handler = _TOOL_HANDLERS.get(name)
    if handler is None:
        raise ValueError(f"MCP_TOOL_NOT_FOUND: unknown tool {name!r}")

    try:
        result = handler(args)
    except KeyError as exc:
        raise ValueError(f"MCP_VALIDATION_ERROR: missing field {exc}") from exc

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
