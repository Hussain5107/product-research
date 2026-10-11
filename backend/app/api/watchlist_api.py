from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product, WatchlistStatus
from app.api.deps import require_access_token

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.post("/add", response_model=dict[str, Any])
async def add_to_watchlist(
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    product_id = payload.get("product_id")
    status_code = payload.get("status", "researching")
    note = payload.get("note", "")

    product_result = await session.execute(select(Product).where(Product.id == product_id))
    product = product_result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    status_row = await session.execute(select(WatchlistStatus).where(WatchlistStatus.code == status_code))
    status = status_row.scalar_one_or_none()
    if status is None:
        raise HTTPException(status_code=400, detail=f"Unknown watchlist status: {status_code}")

    # Simple scalar watchlist tracking stored as JSON note on product for Phase 1.
    existing_note = product.description or ""
    if existing_note:
        existing_note = existing_note + "\n"
    product.description = existing_note + f"[Watchlist {status_code}] {note}".strip()

    await session.commit()
    return {
        "product_id": product.id,
        "status": status_code,
        "note": note,
        "product_name": product.name,
    }


@router.get("/list", response_model=list[dict[str, Any]])
async def list_watchlist(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
    limit: int = Query(100, ge=1, le=200),
) -> list[dict[str, Any]]:
    result = await session.execute(
        select(Product).order_by(Product.created_at.desc()).limit(limit)
    )
    products = result.scalars().all()
    return [_serialize_watchlist_product(p) for p in products]


def _serialize_watchlist_product(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "asin": product.asin,
        "product_url": product.product_url,
        "image_url": product.image_url,
        "supplier_cost": str(product.supplier_cost),
        "shipping_cost": str(product.shipping_cost),
        "suggested_retail_price": str(product.suggested_retail_price),
        "us_warehouse_verified": product.us_warehouse_verified,
        "us_warehouse_verification_status": product.us_warehouse_verification_status,
        "trend_classification": product.trend_classification,
        "viral_potential": product.viral_potential,
        "primary_competition_level": product.primary_competition_level,
        "status": product.status,
        "region_code": product.region.code if product.region else None,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }
