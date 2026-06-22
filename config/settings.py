"""Application settings loaded from environment variables."""

from functools import lru_cache

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "german-bureaucracy-agent"
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = Field(default="change-me")
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    google_api_key: str = Field(default="")
    gemini_model_flash: str = "gemini-2.5-flash"
    gemini_model_pro: str = "gemini-2.5-pro"
    gemini_embedding_model: str = "text-embedding-004"
    use_vertex_ai: bool = False
    google_cloud_project: str = ""
    google_cloud_location: str = "europe-west1"

    database_url: str = (
        "postgresql+asyncpg://bureaucracy:bureaucracy@localhost:5432/bureaucracy"
    )
    redis_url: str = "redis://localhost:6379/0"
    redis_enabled: bool = False

    storage_backend: str = "local"
    storage_local_path: str = "./data/storage"
    mcp_auth_token: str = Field(default="change-me-mcp")

    jwt_secret_key: str = Field(default="change-me-jwt")
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    cors_origins: str = "http://localhost:8501"
    rate_limit_per_minute: int = 20
    max_upload_size_mb: int = 20
    max_pdf_pages: int = 20
    document_retention_days: int = 30
    pii_redaction_enabled: bool = True

    agent_default_locale: str = "en"
    agent_default_bundesland: str = "BE"
    agent_confidence_threshold: float = 0.75
    agent_streaming_enabled: bool = True

    streamlit_api_base_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
