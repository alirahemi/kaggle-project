"""Authentication router — demo JWT token issuance."""

from fastapi import APIRouter, Depends

from apps.api_gateway.middleware.auth import create_access_token
from apps.api_gateway.schemas.common import TokenRequest, TokenResponse
from config.settings import Settings, get_settings

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
async def create_token(
    body: TokenRequest,
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    token = create_access_token(body.user_id, settings, locale=body.locale)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60,
    )
