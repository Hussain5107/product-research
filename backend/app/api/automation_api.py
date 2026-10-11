from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_access_token
from app.database import get_db
from app.models.core import utc_now
from app.models.operations import AutomationJob
from app.models.research import ResearchRun, ResearchStatus

router = APIRouter(prefix="/automation", tags=["automation"])


class AutomationJobCreate(BaseModel):
    name: str = Field(max_length=256)
    job_type: str = Field(default="research", max_length=64)
    schedule_label: str = Field(default="manual", max_length=128)
    query: str = Field(max_length=2048)
    filters: dict[str, Any] | None = None
    status: str = Field(default="paused", max_length=32)
    next_run_note: str | None = Field(default=None, max_length=512)


@router.get("/jobs", response_model=list[dict[str, Any]])
async def list_jobs(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> list[dict[str, Any]]:
    result = await session.execute(select(AutomationJob).order_by(AutomationJob.created_at.desc()))
    return [_serialize_job(job) for job in result.scalars().all()]


@router.post("/jobs", response_model=dict[str, Any])
async def create_job(
    payload: AutomationJobCreate,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    job = AutomationJob(
        name=payload.name,
        job_type=payload.job_type,
        schedule_label=payload.schedule_label,
        query=payload.query,
        filters_json=payload.filters,
        status=payload.status,
        next_run_note=payload.next_run_note,
    )
    session.add(job)
    await session.commit()
    await session.refresh(job)
    return _serialize_job(job)


@router.post("/jobs/{job_id}/run", response_model=dict[str, Any])
async def run_job_now(
    job_id: int,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    result = await session.execute(select(AutomationJob).where(AutomationJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Automation job not found")

    run = ResearchRun(
        name=f"Automation: {job.name}",
        description=job.query,
        marketplace=(job.filters_json or {}).get("marketplace", "both"),
        region_code=(job.filters_json or {}).get("region_code", "US"),
        status=ResearchStatus.queued,
        mode="scheduled_research",
        user_query=job.query,
        filters_json=job.filters_json,
        current_stage="queued",
        progress_message="Queued from automation job. Live execution requires configured connectors.",
    )
    session.add(run)
    await session.flush()
    job.last_run_at = utc_now()
    job.last_result_json = {"research_run_id": run.id, "status": run.status.value}
    job.error_message = None
    await session.commit()
    return {"job": _serialize_job(job), "research_run_id": run.id}


@router.post("/jobs/{job_id}/toggle", response_model=dict[str, Any])
async def toggle_job(
    job_id: int,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    result = await session.execute(select(AutomationJob).where(AutomationJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Automation job not found")
    job.status = "active" if job.status != "active" else "paused"
    await session.commit()
    await session.refresh(job)
    return _serialize_job(job)


def _serialize_job(job: AutomationJob) -> dict[str, Any]:
    return {
        "id": job.id,
        "name": job.name,
        "job_type": job.job_type,
        "schedule_label": job.schedule_label,
        "query": job.query,
        "filters": job.filters_json,
        "status": job.status,
        "last_run_at": job.last_run_at.isoformat() if job.last_run_at else None,
        "next_run_note": job.next_run_note,
        "last_result": job.last_result_json,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }
