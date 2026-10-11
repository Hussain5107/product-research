from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.api.deps import require_access_token
from app.services.financial import CostComponents, calculate_financials, build_sensitivity_table

router = APIRouter(prefix="/profit-calculator", tags=["profit-calculator"])


class CostInput(BaseModel):
    supplier_cost: Decimal = Decimal("0.0000")
    shipping_cost: Decimal = Decimal("0.0000")
    packaging_cost: Decimal = Decimal("0.0000")
    other_cost: Decimal = Decimal("0.0000")
    selling_price: Decimal = Decimal("0.0000")
    marketplace_fee_rate: Decimal = Decimal("0.0000")
    marketplace_fee_fixed: Decimal = Decimal("0.0000")
    payment_fee_rate: Decimal = Decimal("0.029")
    payment_fee_fixed: Decimal = Decimal("0.30")
    expected_return_rate: Decimal = Decimal("0.05")
    ad_cost_cac: Decimal = Decimal("0.0000")


@router.post("/", response_model=dict[str, Any])
async def calculate_profit(
    payload: CostInput,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    components = CostComponents(
        purchase_cost=payload.supplier_cost,
        shipping_cost=payload.shipping_cost,
        packaging_cost=payload.packaging_cost,
        other_landed_cost=payload.other_cost,
        payment_processing_rate=payload.payment_fee_rate,
        payment_processing_fixed=payload.payment_fee_fixed,
        marketplace_fee_rate=payload.marketplace_fee_rate,
        marketplace_fee_fixed=payload.marketplace_fee_fixed,
        expected_return_rate=payload.expected_return_rate,
        customer_acquisition_cost=payload.ad_cost_cac,
    )
    result = calculate_financials(payload.selling_price, components)
    sensitivity = build_sensitivity_table(
        payload.selling_price,
        components,
        [Decimal("5"), Decimal("10"), Decimal("15"), Decimal("20"), Decimal("25")],
    )
    return {
        "landed_cost": str(result.landed_fulfillment_cost),
        "variable_cost": str(result.variable_costs),
        "profit_per_unit": str(result.net_per_unit_before_fixed),
        "margin_percent": str(result.contribution_margin_after_advertising),
        "break_even_cac": str(result.break_even_cac),
        "break_even_roas": str(result.break_even_roas) if result.break_even_roas is not None else None,
        "sensitivity": [
            {
                "cac": str(s["cac"]),
                "contribution_after_advertising": s["contribution_after_advertising"],
                "contribution_margin_after_advertising": s["contribution_margin_after_advertising"],
            }
            for s in sensitivity
        ],
    }


@router.get("/list")
async def list_profit_products(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
    search: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    query = select(Product).order_by(Product.created_at.desc())
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    if status:
        query = query.where(Product.status == status)
    result = await session.execute(query.limit(200))
    return [_serialize_profit_product(p) for p in result.scalars().all()]


def _serialize_profit_product(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "supplier_cost": str(product.supplier_cost),
        "shipping_cost": str(product.shipping_cost),
        "suggested_retail_price": str(product.suggested_retail_price),
        "status": product.status,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }
