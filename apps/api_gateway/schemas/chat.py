"""Concierge chat request and response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: UUID
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    message_id: UUID
    response: str
    sources: list[str] = Field(default_factory=list)
    disclaimer: str
