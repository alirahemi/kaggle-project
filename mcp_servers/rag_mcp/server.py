"""RAG MCP server — knowledge search, glossary, and similar cases."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool

from config.settings import get_settings

SERVER_NAME = "bureaucracy-rag-mcp"
SERVER_VERSION = "1.0.0"

logger = logging.getLogger(__name__)
settings = get_settings()
server = Server(SERVER_NAME)

_GLOSSARY: dict[str, dict[str, Any]] = {
    "bescheid": {
        "term": "Bescheid",
        "definition_de": "Eine behördliche Entscheidung in Schriftform.",
        "definition_en": "An official administrative decision in written form.",
        "related_terms": ["Widerspruch", "Rechtsbehelfsbelehrung"],
    },
    "widerspruch": {
        "term": "Widerspruch",
        "definition_de": "Formeller Rechtsbehelf gegen einen Bescheid.",
        "definition_en": "Formal legal remedy against an administrative decision.",
        "related_terms": ["Bescheid", "Einspruch"],
    },
    "nachforderung": {
        "term": "Nachforderung",
        "definition_de": "Aufforderung, fehlende Unterlagen nachzureichen.",
        "definition_en": "Request to submit missing documents.",
        "related_terms": ["Frist", "Bescheid"],
    },
}

_SAMPLE_CASES: list[dict[str, Any]] = [
    {
        "template_id": "jc-nachforderung-001",
        "authority": "jobcenter",
        "letter_type": "nachforderung",
        "snippet": "Nachreichung von Gehaltsabrechnungen bis zum 15.",
    },
    {
        "template_id": "fa-einspruch-001",
        "authority": "finanzamt",
        "letter_type": "einspruch",
        "snippet": "Einspruch gegen den Steuerbescheid einlegen.",
    },
    {
        "template_id": "kk-familienversicherung-001",
        "authority": "krankenkasse",
        "letter_type": "familienversicherung",
        "snippet": "Antrag auf Familienversicherung ohne eigenes Einkommen.",
    },
]

TOOLS: list[Tool] = [
    Tool(
        name="search_knowledge",
        description="Hybrid semantic and keyword search over curated corpus.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "authority": {
                    "type": ["string", "null"],
                    "description": "Filter by authority (e.g. jobcenter)",
                },
                "limit": {"type": "integer", "description": "Max results", "default": 5},
            },
            "required": ["query"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "source": {"type": "string"},
                            "score": {"type": "number"},
                        },
                        "required": ["title", "content", "source", "score"],
                    },
                }
            },
            "required": ["results"],
        },
    ),
    Tool(
        name="get_glossary_term",
        description="Lookup bilingual glossary entry.",
        inputSchema={
            "type": "object",
            "properties": {
                "term": {"type": "string", "description": "German bureaucratic term"},
                "locale": {
                    "type": "string",
                    "description": "Preferred definition locale",
                    "default": settings.agent_default_locale,
                },
            },
            "required": ["term"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "term": {"type": "string"},
                "definition_de": {"type": "string"},
                "definition_en": {"type": "string"},
                "related_terms": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["term", "definition_de", "definition_en", "related_terms"],
        },
    ),
    Tool(
        name="find_similar_cases",
        description="Embedding search on synthetic letter templates.",
        inputSchema={
            "type": "object",
            "properties": {
                "text_snippet": {"type": "string", "description": "Letter excerpt"},
                "limit": {"type": "integer", "description": "Max matches", "default": 3},
            },
            "required": ["text_snippet"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "matches": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "template_id": {"type": "string"},
                            "authority": {"type": "string"},
                            "letter_type": {"type": "string"},
                            "score": {"type": "number"},
                        },
                        "required": ["template_id", "authority", "letter_type", "score"],
                    },
                }
            },
            "required": ["matches"],
        },
    ),
]


def _search_knowledge(
    query: str, authority: str | None = None, limit: int = 5
) -> dict[str, Any]:
    results = [
        {
            "title": f"Knowledge stub: {query[:40]}",
            "content": (
                f"[stub] Curated guidance for '{query}'. "
                "Production will use pgvector hybrid search."
            ),
            "source": f"knowledge/authorities/{authority or 'general'}/faq.md",
            "score": 0.89,
        }
    ]
    if authority:
        results.append(
            {
                "title": f"{authority.title()} — official process overview",
                "content": f"[stub] Authority-specific FAQ for {authority}.",
                "source": f"knowledge/authorities/{authority}/overview.md",
                "score": 0.82,
            }
        )
    return {"results": results[:limit]}


def _get_glossary_term(term: str, locale: str = "en") -> dict[str, Any]:
    entry = _GLOSSARY.get(term.lower())
    if entry:
        return entry
    return {
        "term": term,
        "definition_de": f"[stub] Keine Definition für '{term}' im Glossar.",
        "definition_en": f"[stub] No glossary entry for '{term}' (locale={locale}).",
        "related_terms": [],
    }


def _find_similar_cases(text_snippet: str, limit: int = 3) -> dict[str, Any]:
    snippet_lower = text_snippet.lower()
    matches = []
    for idx, case in enumerate(_SAMPLE_CASES):
        score = 0.91 - (idx * 0.05)
        if any(word in snippet_lower for word in case["snippet"].lower().split()[:3]):
            score = min(0.98, score + 0.05)
        matches.append(
            {
                "template_id": case["template_id"],
                "authority": case["authority"],
                "letter_type": case["letter_type"],
                "score": round(score, 2),
            }
        )
    return {"matches": matches[:limit]}


_TOOL_HANDLERS: dict[str, Any] = {
    "search_knowledge": lambda args: _search_knowledge(
        args["query"], args.get("authority"), args.get("limit", 5)
    ),
    "get_glossary_term": lambda args: _get_glossary_term(
        args["term"], args.get("locale", settings.agent_default_locale)
    ),
    "find_similar_cases": lambda args: _find_similar_cases(
        args["text_snippet"], args.get("limit", 3)
    ),
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
            uri="knowledge://glossary/index",
            name="Glossary index",
            description="Bilingual bureaucratic glossary",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    if uri.startswith("knowledge://glossary/"):
        term = uri.removeprefix("knowledge://glossary/")
        if term == "index":
            return json.dumps(list(_GLOSSARY.keys()), ensure_ascii=False)
        return json.dumps(_get_glossary_term(term), ensure_ascii=False)

    if uri.startswith("knowledge://authority/") and uri.endswith("/faq"):
        parts = uri.removeprefix("knowledge://authority/").removesuffix("/faq")
        authority = parts.split("/")[0]
        return json.dumps(
            _search_knowledge(f"{authority} FAQ", authority=authority, limit=3),
            ensure_ascii=False,
        )

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
