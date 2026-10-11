from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import require_access_token
from app.models.product import Product
from app.models.research import ResearchRun, OpportunityScore

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def dashboard_summary(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    product_count = await session.scalar(select(func.count(Product.id)))
    score_rows = await session.execute(select(OpportunityScore.marketplace, OpportunityScore.total_score))
    scores = score_rows.all()

    high_potential = sum(1 for _, total in scores if total and int(total) >= 70)
    amazon_scores = [int(total) for mp, total in scores if mp == "amazon" and total is not None]
    shopify_scores = [int(total) for mp, total in scores if mp == "shopify" and total is not None]

    latest_run = await session.scalar(
        select(ResearchRun.created_at).order_by(ResearchRun.created_at.desc()).limit(1)
    )

    return {
        "productsAnalyzed": int(product_count or 0),
        "newOpportunities": high_potential,
        "highPotentialProducts": high_potential,
        "verifiedUSWarehouseProducts": 0,
        "trendingProducts": 0,
        "watchlistAlerts": 0,
        "previousPeriod": None,
        "lastResearchRun": latest_run.isoformat() if latest_run else None,
        "scoreCoverage": {
            "amazonProductsScored": len(amazon_scores),
            "shopifyProductsScored": len(shopify_scores),
        },
    }


@router.get("/trends")
async def dashboard_trends(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
    limit: int = Query(30, ge=1, le=180),
) -> list[dict[str, Any]]:
    runs_result = await session.execute(
        select(ResearchRun).order_by(ResearchRun.created_at.asc()).limit(limit)
    )
    runs = runs_result.scalars().all()

    points: list[dict[str, Any]] = []
    for run in runs:
        run_scores = await session.execute(
            select(OpportunityScore.total_score).where(OpportunityScore.research_run_id == run.id)
        )
        values = [int(v) for (v,) in run_scores if v is not None]
        average = round(sum(values) / len(values)) if values else 0
        points.append(
            {
                "date": run.created_at.date().isoformat() if run.created_at else "",
                "opportunityScore": average,
                "verifiedProducts": 0,
                "trendingCandidates": int(run.candidates_discovered or 0),
            }
        )
    return points


@router.get("/categories")
async def dashboard_categories(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> list[dict[str, Any]]:
    category_counts = await session.execute(
        select(Product.category, func.count(Product.id))
        .group_by(Product.category)
        .order_by(func.count(Product.id).desc())
        .limit(10)
    )
    return [
        {"category": (category or "Unknown"), "change": int(count), "score": 0}
        for category, count in category_counts.all()
    ]


@router.get("/last-research-run")
async def last_research_run(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> str:
    result = await session.execute(
        select(ResearchRun.created_at).order_by(ResearchRun.created_at.desc()).limit(1)
    )
    value = result.scalar_one_or_none()
    return value.isoformat() if value else ""
