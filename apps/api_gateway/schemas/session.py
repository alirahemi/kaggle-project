"""Session request and response schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from apps.api_gateway.schemas.common import SessionStatusEnum


class CreateSessionRequest(BaseModel):
    locale: str = "en"
    bundesland: str = "BE"


class SessionResponse(BaseModel):
    session_id: UUID
    created_at: datetime
    locale: str
    bundesland: str
    status: SessionStatusEnum = SessionStatusEnum.ACTIVE
    document_id: UUID | None = None
    analysis_id: UUID | None = None
