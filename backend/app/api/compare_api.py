from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.api.deps import require_access_token
from app.services.financial import CostComponents, calculate_financials
from app.services.financial import build_sensitivity_table

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("/candidates", response_model=list[dict[str, Any]])
async def compare_candidates(
    product_ids: list[int] = Query(..., min_length=1, max_length=10),
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> list[dict[str, Any]]:
    result = await session.execute(select(Product).where(Product.id.in_(product_ids)))
    products = {p.id: p for p in result.scalars().all()}
    missing = set(product_ids) - set(products.keys())
    if missing:
        raise HTTPException(status_code=404, detail=f"Products not found: {sorted(missing)}")
    return [_serialize_compare_product(products[pid]) for pid in product_ids]


def _serialize_compare_product(product: Product) -> dict[str, Any]:
    # Avoid session access here; return basic comparison data.
    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "asin": product.asin,
        "image_url": product.image_url,
        "thumbnail_url": product.thumbnail_url,
        "supplier_cost": str(product.supplier_cost),
        "shipping_cost": str(product.shipping_cost),
        "suggested_retail_price": str(product.suggested_retail_price),
        "us_warehouse_verified": product.us_warehouse_verified,
        "us_warehouse_verification_status": product.us_warehouse_verification_status,
        "trend_classification": product.trend_classification,
        "viral_potential": product.viral_potential,
        "primary_competition_level": product.primary_competition_level,
        "amazon_fulfillment_suitable": product.amazon_fulfillment_suitable,
        "region_code": product.region.code if product.region else None,
    }


@router.get("/financials", response_model=list[dict[str, Any]])
async def compare_financials(
    product_ids: list[int] = Query(..., min_length=1, max_length=10),
    selling_price: str | None = Query(None),
    customer_acquisition_cost: str | None = Query(None),
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> list[dict[str, Any]]:
    result = await session.execute(select(Product).where(Product.id.in_(product_ids)))
    products = {p.id: p for p in result.scalars().all()}
    missing = set(product_ids) - set(products.keys())
    if missing:
        raise HTTPException(status_code=404, detail=f"Products not found: {sorted(missing)}")

    price = selling_price
    cac = customer_acquisition_cost
    return [
        {
            "product_id": pid,
            "product_name": p.name,
            "financials": _calculate_financials_for_product(p, price, cac),
        }
        for pid, p in sorted(products.items())
    ]


def _calculate_financials_for_product(product: Product, price: str | None, cac: str | None) -> dict[str, Any]:
    selling_price = price if price else (product.suggested_retail_price or Decimal("0"))
    if isinstance(selling_price, str):
        selling_price = Decimal(selling_price)
    customer_acquisition_cost = Decimal(cac) if cac else Decimal("0")

    components = CostComponents(
        purchase_cost=product.supplier_cost,
        shipping_cost=product.shipping_cost,
        packaging_cost=product.packaging_cost,
        other_landed_cost=product.other_landed_cost,
        payment_processing_rate=Decimal("0.029"),
        payment_processing_fixed=Decimal("0.30"),
        marketplace_fee_rate=Decimal("0"),
        marketplace_fee_fixed=Decimal("0"),
        expected_return_rate=Decimal("0.05"),
        customer_acquisition_cost=customer_acquisition_cost,
        advertising_rate=None,
    )
    result = calculate_financials(
        selling_price,
        components,
    )
    return {
        "selling_price": str(result.selling_price),
        "landed_fulfillment_cost": str(result.landed_fulfillment_cost),
        "contribution_before_advertising": str(result.contribution_before_advertising),
        "contribution_after_advertising": str(result.contribution_after_advertising),
        "contribution_margin_after_advertising": str(result.contribution_margin_after_advertising),
        "break_even_cac": str(result.break_even_cac),
        "break_even_roas": str(result.break_even_roas) if result.break_even_roas else None,
        "sensitivity": _build_sensitivity(selling_price, components, result.advertising_cost),
    }


def _build_sensitivity(
    selling_price: Decimal,
    components: CostComponents,
    base_cac: Decimal,
) -> list[dict[str, Any]]:
    values = [
        Decimal("0"),
        Decimal("5"),
        Decimal("10"),
        base_cac,
        base_cac + Decimal("5"),
    ]
    unique_values = sorted({value for value in values if value >= Decimal("0")})
    rows = build_sensitivity_table(
        selling_price,
        components,
        unique_values,
    )
    return [
        {
            "cac": str(row.cac),
            "contribution_after_advertising": str(row.contribution_after_advertising),
            "contribution_margin_after_advertising": str(row.contribution_margin_after_advertising),
        }
        for row in rows
    ]
