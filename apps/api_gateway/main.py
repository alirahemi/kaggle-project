"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.api_gateway.middleware.auth import auth_middleware
from apps.api_gateway.middleware.rate_limit import rate_limit_middleware
from apps.api_gateway.routers import (
    analysis,
    auth,
    chat,
    documents,
    health,
    sessions,
    users,
)
from apps.api_gateway.schemas.common import ErrorDetail, ErrorResponse
from config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="REST + SSE API for multi-agent letter analysis",
        lifespan=lifespan,
        debug=settings.app_debug,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(rate_limit_middleware)
    app.middleware("http")(auth_middleware)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(sessions.router)
    app.include_router(documents.router)
    app.include_router(analysis.router)
    app.include_router(chat.router)
    app.include_router(users.router)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="internal_error",
                    message="An unexpected error occurred",
                    details={"path": str(request.url.path)},
                )
            ).model_dump(),
        )

    return app


app = create_app()


def main() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "apps.api_gateway.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_debug,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
