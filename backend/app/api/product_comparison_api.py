from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.product import Product
from app.models.supplier import SupplierProduct
from app.api.deps import require_access_token
from app.services.financial import CostComponents, calculate_financials

router = APIRouter(prefix="/product-comparison", tags=["product-comparison"])


@router.get("/candidates")
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
    suppliers = []
    for sp in product.supplier_products or []:
        supplier = sp.supplier
        suppliers.append(
            {
                "supplier_name": supplier.name if supplier else None,
                "supplier_platform": supplier.platform if supplier else None,
                "supplier_url": supplier.website_url if supplier else None,
                "warehouse_origin": sp.warehouse_origin,
                "stock_quantity": sp.stock_quantity,
                "processing_time_days": sp.processing_time_days,
                "delivery_estimate_days": sp.delivery_estimate_days,
                "shipping_service": sp.shipping_service,
                "evidence_status": sp.evidence_status,
                "verification_timestamp": sp.verification_timestamp.isoformat()
                if sp.verification_timestamp
                else None,
            }
        )
    return {
        "id": product.id,
        "name": product.name,
        "category": product.category,
        "asin": product.asin,
        "image_url": product.image_url,
        "supplier_cost": str(product.supplier_cost),
        "shipping_cost": str(product.shipping_cost),
        "suggested_retail_price": str(product.suggested_retail_price),
        "status": product.status,
        "primary_competition_level": product.primary_competition_level,
        "viral_potential": product.viral_potential,
        "suppliers": suppliers,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }


@router.get("/financials")
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

    price = Decimal(selling_price) if selling_price else product.suggested_retail_price or Decimal("0")
    cac = Decimal(customer_acquisition_cost) if customer_acquisition_cost else Decimal("0")

    return [
        {
            "product_id": pid,
            "product_name": p.name,
            "financials": _calculate_financials_for_product(p, price, cac),
        }
        for pid, p in sorted(products.items())
    ]


def _calculate_financials_for_product(
    product: Product, price: Decimal, cac: Decimal
) -> dict[str, Any]:
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
        customer_acquisition_cost=cac,
    )
    result = calculate_financials(price, components)
    return {
        "landed_fulfillment_cost": str(result.landed_fulfillment_cost),
        "variable_costs": str(result.variable_costs),
        "contribution_before_advertising": str(result.contribution_before_advertising),
        "contribution_after_advertising": str(result.contribution_after_advertising),
        "contribution_margin_after_advertising": str(result.contribution_margin_after_advertising),
        "break_even_cac": str(result.break_even_cac),
        "break_even_roas": str(result.break_even_roas) if result.break_even_roas else None,
    }
