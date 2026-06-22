"""Simple in-memory rate limiting middleware."""

import time
from collections import defaultdict, deque

from fastapi import Request, status
from fastapi.responses import JSONResponse

from apps.api_gateway.schemas.common import ErrorDetail, ErrorResponse
from config.settings import get_settings

_request_log: dict[str, deque[float]] = defaultdict(deque)


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


async def rate_limit_middleware(request: Request, call_next):
    """Limit requests per client IP using a sliding one-minute window."""
    if request.url.path == "/health":
        return await call_next(request)

    settings = get_settings()
    limit = settings.rate_limit_per_minute
    key = _client_key(request)
    now = time.monotonic()
    window = _request_log[key]

    while window and now - window[0] > 60:
        window.popleft()

    if len(window) >= limit:
        body = ErrorResponse(
            error=ErrorDetail(code="rate_limit_exceeded", message="Rate limit exceeded. Try again in a minute.")
        )
        return JSONResponse(status_code=status.HTTP_429_TOO_MANY_REQUESTS, content=body.model_dump())

    window.append(now)
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(max(0, limit - len(window)))
    return response
