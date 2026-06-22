"""Document upload and metadata router."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from apps.api_gateway.middleware.auth import get_current_user_id
from apps.api_gateway.schemas.common import DocumentStatusEnum
from apps.api_gateway.schemas.document import DocumentMetadata, DocumentResponse
from config.settings import Settings, get_settings

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

_documents: dict[UUID, DocumentMetadata] = {}
_document_previews: dict[UUID, str] = {}


def _redact_preview(text: str, max_len: int = 500) -> str:
    preview = text[:max_len]
    for token in ("straße", "str.", "plz", "iban"):
        preview = preview.replace(token, "[REDACTED]")
    return preview


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    session_id: UUID = Form(...),
    user_id: str = Depends(get_current_user_id),
    settings: Settings = Depends(get_settings),
) -> DocumentResponse:
    if file.filename is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename required")

    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_size_mb} MB limit",
        )

    storage_dir = Path(settings.storage_local_path) / str(session_id)
    storage_dir.mkdir(parents=True, exist_ok=True)
    document_id = uuid4()
    dest = storage_dir / f"{document_id}_{file.filename}"
    dest.write_bytes(content)

    text_preview = content.decode("utf-8", errors="ignore") or file.filename
    preview = _redact_preview(text_preview) if settings.pii_redaction_enabled else text_preview[:500]
    page_count = max(1, len(content) // 3000)

    now = datetime.now(UTC)
    metadata = DocumentMetadata(
        document_id=document_id,
        filename=file.filename,
        page_count=page_count,
        status=DocumentStatusEnum.READY,
        created_at=now,
    )
    _documents[document_id] = metadata
    _document_previews[document_id] = preview

    return DocumentResponse(
        document_id=document_id,
        session_id=session_id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        page_count=page_count,
        redacted_preview=preview,
        pii_redacted=settings.pii_redaction_enabled,
        retention_expires_at=now + timedelta(days=settings.document_retention_days),
    )


@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document(
    document_id: UUID,
    user_id: str = Depends(get_current_user_id),
) -> DocumentMetadata:
    document = _documents.get(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return document
