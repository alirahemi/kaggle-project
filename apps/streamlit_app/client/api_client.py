"""HTTP client for the FastAPI gateway."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from config.settings import Settings, get_settings


class ApiClientError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"API error {status_code}: {message}")


class ApiClient:
    def __init__(self, settings: Settings | None = None, token: str | None = None):
        self.settings = settings or get_settings()
        self.base_url = self.settings.streamlit_api_base_url.rstrip("/")
        self._token = token

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _handle(self, response: httpx.Response) -> Any:
        if response.is_success:
            if response.status_code == 204:
                return None
            return response.json()
        detail = response.text
        try:
            payload = response.json()
            detail = payload.get("detail", payload)
        except Exception:
            pass
        raise ApiClientError(response.status_code, str(detail))

    def health(self) -> dict[str, Any]:
        with httpx.Client(timeout=30.0) as client:
            return self._handle(client.get(f"{self.base_url}/health"))

    def create_token(self, user_id: str, locale: str = "en") -> dict[str, Any]:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base_url}/api/v1/auth/token",
                json={"user_id": user_id, "locale": locale},
            )
            return self._handle(response)

    def create_session(self, locale: str = "en", bundesland: str = "BE") -> dict[str, Any]:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{self.base_url}/api/v1/sessions",
                json={"locale": locale, "bundesland": bundesland},
                headers=self._headers(),
            )
            return self._handle(response)

    def upload_document(self, session_id: UUID | str, file_name: str, content: bytes) -> dict[str, Any]:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/api/v1/documents",
                headers=self._headers(),
                data={"session_id": str(session_id)},
                files={"file": (file_name, content)},
            )
            return self._handle(response)

    def start_analysis(self, session_id: UUID | str, document_id: UUID | str) -> dict[str, Any]:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/api/v1/analysis",
                json={"session_id": str(session_id), "document_id": str(document_id)},
                headers=self._headers(),
            )
            return self._handle(response)

    def get_analysis(self, analysis_id: UUID | str) -> dict[str, Any]:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                f"{self.base_url}/api/v1/analysis/{analysis_id}",
                headers=self._headers(),
            )
            return self._handle(response)

    def chat(self, session_id: UUID | str, message: str) -> dict[str, Any]:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{self.base_url}/api/v1/chat",
                json={"session_id": str(session_id), "message": message},
                headers=self._headers(),
            )
            return self._handle(response)
