"""Document MCP server — parsing, OCR, PII redaction, and storage."""

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
from mcp_servers.document_mcp.tools import parser, pii, storage

SERVER_NAME = "bureaucracy-document-mcp"
SERVER_VERSION = "1.0.0"

logger = logging.getLogger(__name__)
settings = get_settings()
server = Server(SERVER_NAME)

TOOLS: list[Tool] = [
    Tool(
        name="parse_document",
        description="Parse PDF or plain text into structured content.",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the document file"},
                "max_pages": {
                    "type": "integer",
                    "description": "Maximum pages to parse",
                    "default": settings.max_pdf_pages,
                },
            },
            "required": ["file_path"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "page_count": {"type": "integer"},
                "metadata": {"type": "object"},
            },
            "required": ["text", "page_count", "metadata"],
        },
    ),
    Tool(
        name="ocr_document",
        description="OCR for scanned PDFs and images.",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the image or PDF"},
                "language": {
                    "type": "string",
                    "description": "Tesseract language code",
                    "default": "deu",
                },
            },
            "required": ["file_path"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "confidence": {"type": "number"},
            },
            "required": ["text", "confidence"],
        },
    ),
    Tool(
        name="redact_pii",
        description="Redact names, addresses, Steuer-ID, and Aktenzeichen patterns.",
        inputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to redact"},
                "preserve_aktenzeichen": {
                    "type": "boolean",
                    "description": "Keep Aktenzeichen references intact",
                    "default": False,
                },
            },
            "required": ["text"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "redacted_text": {"type": "string"},
                "redaction_map": {"type": "object"},
                "pii_found": {"type": "boolean"},
            },
            "required": ["redacted_text", "redaction_map", "pii_found"],
        },
    ),
    Tool(
        name="store_document",
        description="Encrypt and store a document; returns an opaque doc_id.",
        inputSchema={
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the source file"},
                "user_id": {"type": "string", "description": "Owner user UUID"},
                "content_type": {
                    "type": "string",
                    "description": "MIME type",
                    "default": "application/pdf",
                },
            },
            "required": ["file_path", "user_id"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "doc_id": {"type": "string"},
                "storage_key": {"type": "string"},
                "retention_expires_at": {"type": "string", "format": "date-time"},
            },
            "required": ["doc_id", "storage_key", "retention_expires_at"],
        },
    ),
    Tool(
        name="get_document_text",
        description="Retrieve document text (role-gated).",
        inputSchema={
            "type": "object",
            "properties": {
                "doc_id": {"type": "string", "description": "Document UUID"},
                "redacted_only": {
                    "type": "boolean",
                    "description": "Return redacted text only",
                    "default": True,
                },
            },
            "required": ["doc_id"],
        },
        outputSchema={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "doc_id": {"type": "string"},
            },
            "required": ["text", "doc_id"],
        },
    ),
]

_TOOL_HANDLERS: dict[str, Any] = {
    "parse_document": lambda args: parser.parse_document(
        args["file_path"], args.get("max_pages")
    ),
    "ocr_document": lambda args: parser.ocr_document(
        args["file_path"], args.get("language", "deu")
    ),
    "redact_pii": lambda args: pii.redact_pii(
        args["text"], args.get("preserve_aktenzeichen", False)
    ),
    "store_document": lambda args: storage.store_document(
        args["file_path"],
        args["user_id"],
        args.get("content_type", "application/pdf"),
    ),
    "get_document_text": lambda args: storage.get_document_text(
        args["doc_id"], args.get("redacted_only", True)
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
    except OSError as exc:
        raise ValueError(f"MCP_STORAGE_ERROR: {exc}") from exc

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]


@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri="document://catalog",
            name="Document metadata catalog",
            description="Index of stored document metadata (no content)",
            mimeType="application/json",
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    if uri.startswith("document://") and uri.endswith("/metadata"):
        doc_id = uri.removeprefix("document://").removesuffix("/metadata")
        return json.dumps(storage.get_document_metadata(doc_id), ensure_ascii=False)
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
