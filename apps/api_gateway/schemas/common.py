"""Shared API schemas and enumerations."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AuthorityEnum(StrEnum):
    JOBCENTER = "jobcenter"
    AUSLAENDERBEHOERDE = "auslaenderbehoerde"
    FINANZAMT = "finanzamt"
    KRANKENKASSE = "krankenkasse"
    OTHER = "other"


class LetterTypeEnum(StrEnum):
    BEWILLIGUNGSBESCHEID = "bewilligungsbescheid"
    ABLEHNUNGSBESCHEID = "ablehnungsbescheid"
    NACHFORDERUNG = "nachforderung"
    FRISTSETZUNG = "fristsetzung"
    TERMIN = "termin"
    MAHNUNG = "mahnung"
    BESCHEID = "bescheid"
    OTHER = "other"


class AnalysisStatusEnum(StrEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_CONFIRMATION = "requires_confirmation"


class ConfidenceLevelEnum(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    REVIEW_RECOMMENDED = "review_recommended"


class SessionStatusEnum(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


class DocumentStatusEnum(StrEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    READY = "ready"
    DELETED = "deleted"


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    services: dict[str, str] = Field(default_factory=dict)


class TokenRequest(BaseModel):
    user_id: str
    locale: str = "en"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
