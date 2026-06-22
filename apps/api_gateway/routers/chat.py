"""Concierge follow-up chat router."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends

from apps.api_gateway.middleware.auth import get_current_user_id
from apps.api_gateway.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

DISCLAIMER = (
    "This response is AI-generated and does not constitute legal advice. "
    "Verify deadlines with the original letter and official sources."
)


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user_id: str = Depends(get_current_user_id),
) -> ChatResponse:
    reply = (
        f"Regarding your question about session {body.session_id}: "
        f"{body.message.strip()[:200]} — "
        "I recommend checking the deadline on your letter and contacting "
        "the issuing authority if anything is unclear."
    )
    return ChatResponse(
        message_id=uuid4(),
        response=reply,
        sources=["knowledge/authorities/jobcenter/faq.md"],
        disclaimer=DISCLAIMER,
    )
