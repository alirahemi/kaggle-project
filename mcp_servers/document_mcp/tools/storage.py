"""Document storage tool stubs."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from config.settings import get_settings

_INDEX_FILE = "document_index.json"


def _storage_root() -> Path:
    settings = get_settings()
    root = Path(settings.storage_local_path)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _load_index() -> dict[str, Any]:
    index_path = _storage_root() / _INDEX_FILE
    if not index_path.exists():
        return {}
    return json.loads(index_path.read_text(encoding="utf-8"))


def _save_index(index: dict[str, Any]) -> None:
    index_path = _storage_root() / _INDEX_FILE
    index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")


def store_document(
    file_path: str,
    user_id: str,
    content_type: str = "application/pdf",
) -> dict[str, Any]:
    """Encrypt and store a document; returns an opaque doc_id."""
    settings = get_settings()
    source = Path(file_path)
    doc_id = str(uuid.uuid4())
    storage_key = f"{user_id}/{doc_id}{source.suffix or '.bin'}"
    target = _storage_root() / storage_key
    target.parent.mkdir(parents=True, exist_ok=True)

    if source.exists():
        target.write_bytes(source.read_bytes())
    else:
        target.write_text(
            f"[stub] placeholder for missing source: {file_path}",
            encoding="utf-8",
        )

    retention_expires_at = (
        datetime.now(UTC) + timedelta(days=settings.document_retention_days)
    ).isoformat()

    index = _load_index()
    index[doc_id] = {
        "storage_key": storage_key,
        "user_id": user_id,
        "content_type": content_type,
        "retention_expires_at": retention_expires_at,
        "text": f"[stub] stored content for {source.name}",
    }
    _save_index(index)

    return {
        "doc_id": doc_id,
        "storage_key": storage_key,
        "retention_expires_at": retention_expires_at,
    }


def get_document_text(doc_id: str, redacted_only: bool = True) -> dict[str, Any]:
    """Retrieve document text (role-gated stub)."""
    index = _load_index()
    record = index.get(doc_id)
    if not record:
        return {
            "text": "",
            "doc_id": doc_id,
            "error": "Document not found",
        }

    text = record.get("text", "")
    if redacted_only:
        from mcp_servers.document_mcp.tools.pii import redact_pii

        text = redact_pii(text).get("redacted_text", text)

    return {"text": text, "doc_id": doc_id}


def get_document_metadata(doc_id: str) -> dict[str, Any]:
    """Return metadata for a stored document without content."""
    index = _load_index()
    record = index.get(doc_id)
    if not record:
        return {"doc_id": doc_id, "found": False}

    return {
        "doc_id": doc_id,
        "found": True,
        "user_id": record.get("user_id"),
        "content_type": record.get("content_type"),
        "storage_key": record.get("storage_key"),
        "retention_expires_at": record.get("retention_expires_at"),
    }
