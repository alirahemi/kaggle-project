"""Bureaucracy MCP server — glossary_lookup and deadline_calculator."""

from __future__ import annotations

import asyncio
import json
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp_servers.bureaucracy_mcp.tools import (
    business_days_until,
    deadline_calculator,
    glossary_lookup,
)

logger = logging.getLogger(__name__)
server = Server("bureaucracy-mcp")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="glossary_lookup",
            description="Look up a German bureaucracy term (e.g. Bescheid, Nachforderung).",
            inputSchema={
                "type": "object",
                "properties": {
                    "term": {"type": "string"},
                    "locale": {"type": "string", "default": "en"},
                },
                "required": ["term"],
            },
        ),
        Tool(
            name="deadline_calculator",
            description="Parse a German deadline (DD.MM.YYYY) and compute days remaining.",
            inputSchema={
                "type": "object",
                "properties": {
                    "deadline_text": {"type": "string"},
                    "reference_date": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["deadline_text"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "glossary_lookup":
        result = glossary_lookup(
            term=arguments["term"],
            locale=arguments.get("locale", "en"),
        )
    elif name == "deadline_calculator":
        result = deadline_calculator(
            deadline_text=arguments["deadline_text"],
            reference_date=arguments.get("reference_date"),
        )
    elif name == "business_days_until":
        result = business_days_until(
            target_iso=arguments["target_iso"],
            from_iso=arguments.get("from_iso"),
        )
    else:
        raise ValueError(f"Unknown tool: {name}")

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
