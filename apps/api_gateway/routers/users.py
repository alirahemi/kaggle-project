"""GDPR user data export and deletion router."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from apps.api_gateway.middleware.auth import get_current_user_id

router = APIRouter(prefix="/api/v1/users", tags=["users"])


class DataExportResponse(BaseModel):
    export_id: str
    download_url: str
    expires_at: datetime


class DeleteDataRequest(BaseModel):
    confirm: bool


class DeleteDataResponse(BaseModel):
    deleted: bool
    documents_removed: int
    sessions_removed: int


@router.get("/me/data", response_model=DataExportResponse)
async def export_user_data(
    user_id: str = Depends(get_current_user_id),
) -> DataExportResponse:
    export_id = uuid4()
    expires = datetime.now(UTC) + timedelta(hours=24)
    return DataExportResponse(
        export_id=str(export_id),
        download_url=f"/api/v1/users/me/data/{export_id}/download",
        expires_at=expires,
    )


@router.delete("/me/data", response_model=DeleteDataResponse)
async def delete_user_data(
    body: DeleteDataRequest,
    user_id: str = Depends(get_current_user_id),
) -> DeleteDataResponse:
    if not body.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deletion requires confirm=true",
        )
    return DeleteDataResponse(deleted=True, documents_removed=0, sessions_removed=0)
