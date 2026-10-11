from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.api.deps import require_access_token

router = APIRouter(prefix="/discovery", tags=["discovery"])


@router.get("/products")
async def list_discovery_products(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
    status: str | None = Query(None),
    category: str | None = None,
    search: str | None = Query(None, min_length=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    query = select(Product).order_by(Product.created_at.desc())
    if status:
        query = query.where(Product.status == status)
    if category:
        query = query.where(Product.category == category)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    result = await session.execute(query.limit(limit).offset(offset))
    return [_serialize_product(p) for p in result.scalars().all()]


def _serialize_product(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "brand": product.brand,
        "asin": product.asin,
        "product_url": product.product_url,
        "image_url": product.image_url,
        "supplier_cost": str(product.supplier_cost),
        "shipping_cost": str(product.shipping_cost),
        "suggested_retail_price": str(product.suggested_retail_price),
        "trend_classification": product.trend_classification,
        "viral_potential": product.viral_potential,
        "primary_competition_level": product.primary_competition_level,
        "status": product.status,
        "region_code": product.region.code if product.region else None,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }
