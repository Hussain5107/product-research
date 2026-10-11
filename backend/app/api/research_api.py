from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.models.supplier import SupplierProduct
from app.api.deps import require_access_token
from app.workers.research import ResearchWorkflow
from app.connectors.registry import default_registry

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/start", response_model=dict[str, Any])
async def start_research(
    name: str = Query("Research Run", min_length=1),
    description: str = Query(""),
    marketplace: str = Query("both"),
    region_code: str = Query("US"),
    mode: str = Query("automatic_discovery"),
    user_query: str = Query(""),
    categories: str = Query(""),
    filters_json: dict[str, Any] | None = None,
    source_names: str = Query(""),
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    from app.models.research import ResearchRun

    if region_code != "US":
        raise HTTPException(status_code=400, detail="Only US region is supported in Phase 1")

    run = ResearchRun(
        name=name,
        description=description,
        marketplace=marketplace,
        region_code=region_code,
        status="queued",
        mode=mode,
        user_query=user_query,
        categories=categories,
        filters_json=filters_json,
        source_names=source_names,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    try:
        workflow = ResearchWorkflow(session, run.id, default_registry())
        result = await workflow.run()
        return {"run_id": run.id, "status": result.get("status"), "details": result}
    except Exception as e:
        await session.refresh(run)
        return {
            "run_id": run.id,
            "status": "failed",
            "details": {
                "status": "failed",
                "errors": [f"Research workflow failed: {e}"],
                "warnings": [
                    "Live discovery connectors are not fully configured yet. Existing saved products can still be reviewed from Product Finder."
                ],
            },
        }


@router.get("/runs", response_model=list[dict[str, Any]])
async def list_research_runs(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
    limit: int = Query(50, ge=1, le=200),
    status_filter: str | None = Query(None),
) -> list[dict[str, Any]]:
    query = select(ResearchRun).order_by(ResearchRun.created_at.desc())
    if status_filter:
        query = query.where(ResearchRun.status == status_filter)
    result = await session.execute(query.limit(limit))
    runs = result.scalars().all()
    return [_serialize_run(r) for r in runs]


@router.get("/runs/{run_id}", response_model=dict[str, Any])
async def get_research_run(
    run_id: int,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    result = await session.execute(select(ResearchRun).where(ResearchRun.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Research run not found")
    return _serialize_run(run)


@router.get("/runs/{run_id}/products", response_model=list[dict[str, Any]])
async def get_run_products(
    run_id: int,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> list[dict[str, Any]]:
    result = await session.execute(
        select(Product)
    )
    products = result.scalars().all()
    return [_serialize_product_basic(p) for p in products]


def _serialize_run(run: ResearchRun) -> dict[str, Any]:
    return {
        "id": run.id,
        "name": run.name,
        "description": run.description,
        "marketplace": run.marketplace,
        "region_code": run.region_code,
        "status": run.status.value if hasattr(run.status, "value") else str(run.status),
        "mode": run.mode,
        "user_query": run.user_query,
        "current_stage": run.current_stage,
        "progress_message": run.progress_message,
        "candidates_discovered": run.candidates_discovered,
        "candidates_rejected": run.candidates_rejected,
        "products_analyzed": run.products_analyzed,
        "suppliers_checked": run.suppliers_checked,
        "estimated_api_cost_usd": str(run.estimated_api_cost_usd),
        "actual_api_cost_usd": str(run.actual_api_cost_usd),
        "research_start": run.research_start.isoformat() if run.research_start else None,
        "research_end": run.research_end.isoformat() if run.research_end else None,
        "sources_checked": run.sources_checked_json or [],
        "warnings": run.warnings or [],
        "errors": run.errors or [],
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


def _serialize_product_basic(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "brand": product.brand,
        "asin": product.asin,
        "product_url": product.product_url,
        "image_url": product.image_url,
        "thumbnail_url": product.thumbnail_url,
        "supplier_cost": str(product.supplier_cost),
        "shipping_cost": str(product.shipping_cost),
        "packaging_cost": str(product.packaging_cost),
        "other_landed_cost": str(product.other_landed_cost),
        "suggested_retail_price": str(product.suggested_retail_price),
        "weight_kg": str(product.weight_kg),
        "is_lightweight": product.is_lightweight,
        "is_fragile": product.is_fragile,
        "contains_liquid": product.contains_liquid,
        "contains_batteries": product.contains_batteries,
        "requires_electricity": product.requires_electricity,
        "us_warehouse_verified": product.us_warehouse_verified,
        "us_warehouse_verification_status": product.us_warehouse_verification_status,
        "us_warehouse_verification_note": product.us_warehouse_verification_note,
        "estimated_delivery_days": product.estimated_delivery_days,
        "amazon_fulfillment_suitable": product.amazon_fulfillment_suitable,
        "amazon_compliance_note": product.amazon_compliance_note,
        "trend_classification": product.trend_classification,
        "viral_potential": product.viral_potential,
        "primary_competition_level": product.primary_competition_level,
        "status": product.status,
        "region_code": product.region.code if product.region else None,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }
