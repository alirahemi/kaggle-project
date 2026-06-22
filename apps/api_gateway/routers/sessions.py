"""Session management router."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api_gateway.middleware.auth import get_current_user_id
from apps.api_gateway.schemas.common import SessionStatusEnum
from apps.api_gateway.schemas.session import CreateSessionRequest, SessionResponse

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])

_sessions: dict[UUID, SessionResponse] = {}


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: CreateSessionRequest,
    user_id: str = Depends(get_current_user_id),
) -> SessionResponse:
    session = SessionResponse(
        session_id=uuid4(),
        created_at=datetime.now(UTC),
        locale=body.locale,
        bundesland=body.bundesland,
        status=SessionStatusEnum.ACTIVE,
    )
    _sessions[session.session_id] = session
    return session


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    user_id: str = Depends(get_current_user_id),
) -> SessionResponse:
    session = _sessions.get(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    user_id: str = Depends(get_current_user_id),
) -> None:
    if session_id not in _sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    del _sessions[session_id]
