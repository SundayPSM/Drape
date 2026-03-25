import uuid
from fastapi import APIRouter, Depends, Request, HTTPException, Query
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
    return TryOnStatusResponse(job_id=job.id, status=job.status)


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


@router.post("/webhooks/replicate")
async def replicate_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Receive Replicate prediction completion webhook."""
    body = await request.body()
    sig = request.headers.get("webhook-secret", "")

    if not tryon_service.verify_replicate_webhook(body, sig):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    import json
    payload = json.loads(body)
    await tryon_service.handle_webhook(payload, db)
    return {"ok": True}
