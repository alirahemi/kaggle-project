"""JWT authentication middleware stub for protected routes."""

from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from apps.api_gateway.schemas.common import ErrorDetail, ErrorResponse
from config.settings import Settings, get_settings

_bearer_scheme = HTTPBearer(auto_error=False)

PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/api/v1/auth/token",
    }
)


def create_access_token(
    user_id: str,
    settings: Settings | None = None,
    locale: str = "en",
) -> str:
    settings = settings or get_settings()
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": user_id,
        "locale": locale,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials, settings)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return str(user_id)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from exc


def _auth_error(message: str, status_code: int = status.HTTP_401_UNAUTHORIZED) -> JSONResponse:
    body = ErrorResponse(error=ErrorDetail(code="unauthorized", message=message))
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(),
        headers={"WWW-Authenticate": "Bearer"},
    )


async def auth_middleware(request: Request, call_next):
    """Reject unauthenticated requests to protected paths."""
    if request.url.path in PUBLIC_PATHS or request.method == "OPTIONS":
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return _auth_error("Authentication required")

    settings = get_settings()
    token = auth_header.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token, settings)
        request.state.user_id = payload.get("sub")
        request.state.locale = payload.get("locale", settings.agent_default_locale)
    except JWTError:
        return _auth_error("Invalid or expired token")

    return await call_next(request)


def parse_uuid(value: str, field_name: str = "id") -> UUID:
    try:
        return UUID(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}: must be a UUID",
        ) from exc
