from __future__ import annotations

import csv
import io
import json
from decimal import Decimal, InvalidOperation
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_access_token
from app.database import get_db
from app.models.core import utc_now
from app.models.product import Product, ProductSource, Region
from app.models.supplier import Supplier, SupplierContact

router = APIRouter(prefix="/imports", tags=["imports"])


class ImportPayload(BaseModel):
    format: str = Field(pattern="^(csv|json)$")
    content: str = Field(min_length=1)
    source_name: str = Field(default="manual_import", max_length=128)
    source_url: str | None = Field(default=None, max_length=2048)


@router.post("/products", response_model=dict[str, Any])
async def import_products(
    payload: ImportPayload,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    rows = _parse_rows(payload)
    region = await _get_or_create_region(session, "US")

    created: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for index, row in enumerate(rows, start=1):
        name = _clean(row.get("name") or row.get("product_name") or row.get("title"))
        if not name:
            skipped.append({"row": index, "reason": "Missing product name"})
            continue

        product = Product(
            region_id=region.id,
            name=name,
            description=_clean(row.get("description")),
            category=_clean(row.get("category")),
            brand=_clean(row.get("brand")),
            product_url=_clean(row.get("product_url") or row.get("url")),
            image_url=_clean(row.get("image_url")),
            thumbnail_url=_clean(row.get("image_url")),
            supplier_cost=_decimal(row.get("supplier_cost") or row.get("cost")),
            shipping_cost=_decimal(row.get("shipping_cost") or row.get("shipping")),
            suggested_retail_price=_decimal(row.get("suggested_retail_price") or row.get("price")),
            trend_classification=_clean(row.get("trend_classification")) or "insufficient_evidence",
            viral_potential=_clean(row.get("viral_potential")) or "low",
            primary_competition_level=_clean(row.get("competition") or row.get("primary_competition_level"))
            or "unknown",
            status=_clean(row.get("status")) or "candidate",
        )
        session.add(product)
        await session.flush()

        source = ProductSource(
            product_id=product.id,
            source_name=payload.source_name,
            source_type="manual_import",
            source_url=payload.source_url or _clean(row.get("source_url")),
            retrieval_timestamp=utc_now(),
            raw_value=json.dumps(row, ensure_ascii=False),
            data_classification="user_supplied",
            observation_period=_clean(row.get("observation_period")),
            notes=_clean(row.get("notes")),
        )
        session.add(source)
        created.append({"id": product.id, "name": product.name})

    await session.commit()
    return {"created_count": len(created), "skipped_count": len(skipped), "created": created, "skipped": skipped}


@router.post("/suppliers", response_model=dict[str, Any])
async def import_suppliers(
    payload: ImportPayload,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    rows = _parse_rows(payload)
    created: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for index, row in enumerate(rows, start=1):
        name = _clean(row.get("name") or row.get("supplier_name") or row.get("company"))
        if not name:
            skipped.append({"row": index, "reason": "Missing supplier name"})
            continue

        platform = _clean(row.get("platform")) or "manual_import"
        existing = await session.execute(select(Supplier).where(Supplier.name == name, Supplier.platform == platform))
        supplier = existing.scalar_one_or_none()
        if supplier is None:
            supplier = Supplier(
                name=name,
                platform=platform,
                website_url=_clean(row.get("website_url") or row.get("url") or row.get("source_url")),
                supports_shopify=_bool(row.get("supports_shopify")),
                supports_automation=_bool(row.get("supports_automation")),
                provides_tracking=_bool(row.get("provides_tracking")),
                supports_returns=_bool(row.get("supports_returns")),
                return_policy_note=_clean(row.get("return_policy_note")),
                us_warehouse_capable=_bool(row.get("us_warehouse_capable") or row.get("us_warehouse")),
                us_warehouse_note=_clean(row.get("us_warehouse_note")),
                reliability_status=_clean(row.get("reliability_status")) or "unassessed",
                reliability_note=_clean(row.get("reliability_note") or row.get("notes")),
            )
            session.add(supplier)
            await session.flush()

        if any(_clean(row.get(field)) for field in ("email", "whatsapp", "phone", "contact_name")):
            contact = SupplierContact(
                supplier_id=supplier.id,
                contact_name=_clean(row.get("contact_name")),
                role_title=_clean(row.get("role_title") or row.get("role")),
                email=_clean(row.get("email")),
                whatsapp=_clean(row.get("whatsapp")),
                phone=_clean(row.get("phone")),
                country=_clean(row.get("country")),
                source_url=payload.source_url or _clean(row.get("source_url")),
                data_classification="user_supplied",
                verification_status=_clean(row.get("verification_status")) or "unverified",
                notes=_clean(row.get("contact_notes")),
            )
            session.add(contact)

        created.append({"id": supplier.id, "name": supplier.name})

    await session.commit()
    return {"created_count": len(created), "skipped_count": len(skipped), "created": created, "skipped": skipped}


def _parse_rows(payload: ImportPayload) -> list[dict[str, Any]]:
    if payload.format == "json":
        try:
            parsed = json.loads(payload.content)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {exc.msg}") from exc
        if isinstance(parsed, dict):
            parsed = parsed.get("items") or parsed.get("rows") or [parsed]
        if not isinstance(parsed, list):
            raise HTTPException(status_code=400, detail="JSON import must be an object, an array, or contain rows/items.")
        return [row for row in parsed if isinstance(row, dict)]

    reader = csv.DictReader(io.StringIO(payload.content))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV import needs a header row.")
    return [dict(row) for row in reader]


async def _get_or_create_region(session: AsyncSession, code: str) -> Region:
    result = await session.execute(select(Region).where(Region.code == code))
    region = result.scalar_one_or_none()
    if region is not None:
        return region
    region = Region(code=code, name=code, currency_code="USD", default_language="en", is_primary=False)
    session.add(region)
    await session.flush()
    return region


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _decimal(value: Any) -> Decimal:
    text = _clean(value)
    if not text:
        return Decimal("0.0000")
    try:
        return Decimal(text.replace("$", "").replace(",", ""))
    except (InvalidOperation, AttributeError):
        return Decimal("0.0000")


def _bool(value: Any) -> bool:
    text = (_clean(value) or "").lower()
    return text in {"1", "true", "yes", "y", "on", "verified"}
