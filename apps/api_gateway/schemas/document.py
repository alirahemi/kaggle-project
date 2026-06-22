"""Document upload and metadata schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from apps.api_gateway.schemas.common import DocumentStatusEnum


class DocumentResponse(BaseModel):
    document_id: UUID
    session_id: UUID
    filename: str
    content_type: str
    page_count: int
    redacted_preview: str
    pii_redacted: bool
    retention_expires_at: datetime


class DocumentMetadata(BaseModel):
    document_id: UUID
    filename: str
    page_count: int
    status: DocumentStatusEnum
    created_at: datetime
