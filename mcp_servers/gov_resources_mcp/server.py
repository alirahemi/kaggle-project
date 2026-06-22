"""Government resources MCP server — forms, contacts, and official links."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool

from config.settings import get_settings

SERVER_NAME = "bureaucracy-gov-resources-mcp"
SERVER_VERSION = "1.0.0"

logger = logging.getLogger(__name__)
settings = get_settings()
server = Server(SERVER_NAME)

_CATALOG_PATH = Path(__file__).parent / "catalog" / "forms.json"

_AUTHORITY_CONTACTS: dict[str, dict[str, Any]] = {
    "auslaenderbehoerde": {
        "general_info_url": "https://www.service.berlin.de/dienstleistungen/aufenthalt/",
        "appointment_hint": "Termin online über das Bürgeramt-/Ausländerbehörde-Portal buchen.",
        "phone_pattern": "+49 30 #### ####",
    },
    "finanzamt": {
        "general_info_url": "https://www.elster.de/",
        "appointment_hint": "ELSTER-Portal für Steuerangelegenheiten nutzen.",
        "phone_pattern": "+49 ### #### ####",
    },
    "jobcenter": {
        "general_info_url": "https://www.arbeitsagentur.de/",
        "appointment_hint": "Termin über das Jobcenter-Portal oder telefonisch vereinbaren.",
        "phone_pattern": "+49 ### #### ####",
    },
    "krankenkasse": {
        "general_info_url": "https://www.gkv-spitzenverband.de/",
        "appointment_hint": "Kontakt über die zuständige Krankenkasse aufnehmen.",
        "phone_pattern": None,
    },
}

_REQUIRED_DOCUMENTS: dict[tuple[str, str], list[dict[str, Any]]] = {
    ("jobcenter", "nachforderung"): [
        {
            "name": "Gehaltsabrechnung",
            "description": "Letzte drei Monatsabrechnungen",
            "required": True,
        },
        {
            "name": "Kontoauszug",
            "description": "Aktueller Kontoauszug der letzten 3 Monate",
            "required": True,
        },
        {
            "name": "Mietvertrag",
            "description": "Bei Wohngeld-/Kosten der Unterkunft-Nachforderung",
            "required": False,
        },
    ],
    ("finanzamt", "einspruch"): [
        {
            "name": "Steuerbescheid",
            "description": "Original oder Kopie des angefochtenen Bescheids",
            "required": True,
        },
        {
            "name": "Begründung",
            "description": "Schriftliche Begründung des Einspruchs",
            "required": True,
        },
    ],
}

_OFFICIAL_LINKS: dict[tuple[str, str], list[dict[str, str]]] = {
    ("krankenkasse", "familienversicherung"): [
        {
            "title": "GKV — Familienversicherung",
            "url": "https://www.gkv-spitzenverband.de/familienversicherung",
        },
        {
            "title": "Bundesministerium für Gesundheit",
            "url": "https://www.bundesgesundheitsministerium.de/",
        },
    ],
    ("jobcenter", "leistungen"): [
        {
            "title": "Bundesagentur für Arbeit — Bürgergeld",
            "url": "https://www.arbeitsagentur.de/arbeitslos-arbeit-finden/buergergeld",
        }
    ],
}


def _load_catalog() -> dict[str, Any]:
    if _CATALOG_PATH.exists():
        return json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    return {"forms": []}


TOOLS: list[Tool] = [
    Tool(
        name="resolve_form",
        description="Map action to official form ID and URL (curated catalog only).",
        inputSchema={
            "type": "object",
            "properties": {
                "authority": {
                    "type": "string",
                    "description": "Authority type (e.g. finanzamt, jobcenter)",
                },
                "action": {
                    "type": "string",
                    "description": "Action identifier (e.g. einspruch_einlegen)",
                },
            },
            "required": ["authority", "action"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "form_id": {"type": "string"},
                "name": {"type": "string"},
                "url": {"type": "string", "format": "uri"},
                "notes": {"type": "string"},
            },
            "required": ["form_id", "name", "url", "notes"],
        },
    ),
    Tool(
        name="get_authority_contact",
        description="Public contact patterns for an authority type.",
        inputSchema={
            "type": "object",
            "properties": {
                "authority": {"type": "string", "description": "Authority type"},
                "bundesland": {
                    "type": "string",
                    "description": "German state code (e.g. BE, BY)",
                    "default": settings.agent_default_bundesland,
                },
            },
            "required": ["authority"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "general_info_url": {"type": "string", "format": "uri"},
                "appointment_hint": {"type": "string"},
                "phone_pattern": {"type": ["string", "null"]},
            },
            "required": ["general_info_url", "appointment_hint", "phone_pattern"],
        },
    ),
    Tool(
        name="list_required_documents",
        description="Checklist template for a letter type.",
        inputSchema={
            "type": "object",
            "properties": {
                "authority": {"type": "string", "description": "Authority type"},
                "letter_type": {
                    "type": "string",
                    "description": "Letter type (e.g. nachforderung)",
                },
            },
            "required": ["authority", "letter_type"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "documents": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "required": {"type": "boolean"},
                        },
                        "required": ["name", "description", "required"],
                    },
                }
            },
            "required": ["documents"],
        },
    ),
    Tool(
        name="get_official_links",
        description="Curated official resource links.",
        inputSchema={
            "type": "object",
            "properties": {
                "authority": {"type": "string", "description": "Authority type"},
                "topic": {"type": "string", "description": "Topic keyword"},
            },
            "required": ["authority", "topic"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "links": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "url": {"type": "string", "format": "uri"},
                        },
                        "required": ["title", "url"],
                    },
                }
            },
            "required": ["links"],
        },
    ),
]


def _resolve_form(authority: str, action: str) -> dict[str, Any]:
    catalog = _load_catalog()
    for form in catalog.get("forms", []):
        if form.get("authority") == authority and form.get("action") == action:
            return {
                "form_id": form["form_id"],
                "name": form["name"],
                "url": form["url"],
                "notes": form.get("notes", ""),
            }
    return {
        "form_id": "UNKNOWN",
        "name": f"[stub] No catalog entry for {authority}/{action}",
        "url": "https://www.service.bund.de/",
        "notes": "Curated catalog miss — verify manually on service.bund.de",
    }


def _get_authority_contact(authority: str, bundesland: str) -> dict[str, Any]:
    contact = _AUTHORITY_CONTACTS.get(
        authority,
        {
            "general_info_url": "https://www.service.bund.de/",
            "appointment_hint": f"[stub] Contact info for {authority} in {bundesland}",
            "phone_pattern": None,
        },
    )
    return contact


def _list_required_documents(authority: str, letter_type: str) -> dict[str, Any]:
    docs = _REQUIRED_DOCUMENTS.get(
        (authority, letter_type),
        [
            {
                "name": "Amtlicher Brief",
                "description": f"[stub] Generic checklist for {authority}/{letter_type}",
                "required": True,
            }
        ],
    )
    return {"documents": docs}


def _get_official_links(authority: str, topic: str) -> dict[str, Any]:
    links = _OFFICIAL_LINKS.get(
        (authority, topic),
        [
            {
                "title": f"[stub] {authority} — {topic}",
                "url": "https://www.service.bund.de/",
            }
        ],
    )
    return {"links": links}


_TOOL_HANDLERS: dict[str, Any] = {
    "resolve_form": lambda args: _resolve_form(args["authority"], args["action"]),
    "get_authority_contact": lambda args: _get_authority_contact(
        args["authority"], args.get("bundesland", settings.agent_default_bundesland)
    ),
    "list_required_documents": lambda args: _list_required_documents(
        args["authority"], args["letter_type"]
    ),
    "get_official_links": lambda args: _get_official_links(args["authority"], args["topic"]),
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


@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="gov://forms/catalog",
            name="Form catalog",
            description="Full curated form catalog JSON",
            mimeType="application/json",
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "gov://forms/catalog":
        return json.dumps(_load_catalog(), ensure_ascii=False, indent=2)
    raise ValueError(f"Unknown resource: {uri}")


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
