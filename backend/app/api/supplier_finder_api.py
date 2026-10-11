from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.models.supplier import Supplier
from app.api.deps import require_access_token

router = APIRouter(prefix="/supplier-finder", tags=["supplier-finder"])


@router.get("/products")
async def list_supplier_products(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
    supplier_id: int | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    products_result = await session.execute(select(Product).order_by(Product.created_at.desc()).limit(limit).offset(offset))
    products = products_result.scalars().all()
    out: list[dict[str, Any]] = []
    for product in products:
        if supplier_id is not None and product.supplier_products is None:
            continue
        out.append(_serialize_product(product, supplier_id))
    return out


def _serialize_product(product: Product, supplier_id: int | None) -> dict[str, Any]:
    suppliers = [sp for sp in (product.supplier_products or []) if supplier_id is None or sp.supplier_id == supplier_id]
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
        "supplier_count": len(suppliers),
        "supplier_ids": [sp.supplier_id for sp in suppliers],
        "status": product.status,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }


@router.get("/suppliers")
async def list_suppliers(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
    platform: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    query = select(Supplier).order_by(Supplier.created_at.desc()).limit(limit).offset(offset)
    if platform:
        query = query.where(Supplier.platform == platform)
    result = await session.execute(query)
    return [{"id": s.id, "name": s.name, "platform": s.platform, "website_url": s.website_url} for s in result.scalars().all()]
