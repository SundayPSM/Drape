import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models.user import User
from app.dependencies import get_current_user
from app.schemas.tryon import TryOnSubmitRequest, TryOnJobResponse, TryOnStatusResponse
from app.services import tryon_service

router = APIRouter(prefix="/tryon", tags=["tryon"])


@router.post("/submit", response_model=TryOnStatusResponse, status_code=202)
async def submit_tryon(
    data: TryOnSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = await tryon_service.submit_tryon(current_user.id, data, db)
    return TryOnStatusResponse(
        job_id=job.id,
        status=job.status,
        result_url=job.result_url,
        error_message=job.error_message,
        fit_confidence_pct=job.fit_confidence_pct,
        suggested_size=job.suggested_size,
        fit_type=job.fit_type,
        fit_notes=job.fit_notes,
    )


@router.get("/{job_id}/status", response_model=TryOnStatusResponse)
async def get_tryon_status(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await tryon_service.get_job_status(job_id, current_user.id, db)


@router.get("/history", response_model=list[TryOnJobResponse])
async def get_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await tryon_service.get_user_history(current_user.id, db, page, page_size)


@router.patch("/{job_id}/save", response_model=TryOnJobResponse)
async def save_look(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await tryon_service.save_look(job_id, current_user.id, db)


