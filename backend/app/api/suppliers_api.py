from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_access_token
from app.database import get_db
from app.models.supplier import Supplier, SupplierContact, SupplierOutreach, SupplierProduct

router = APIRouter(prefix="/suppliers", tags=["suppliers"])


class SupplierCreate(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    platform: str = Field(default="manual_entry", max_length=128)
    website_url: HttpUrl | None = None
    supports_shopify: bool = False
    supports_automation: bool = False
    provides_tracking: bool = False
    supports_returns: bool = False
    return_policy_note: str | None = None
    us_warehouse_capable: bool = False
    us_warehouse_note: str | None = None
    reliability_status: str = Field(default="unassessed", max_length=32)
    reliability_note: str | None = None


class SupplierContactCreate(BaseModel):
    contact_name: str | None = Field(default=None, max_length=256)
    role_title: str | None = Field(default=None, max_length=256)
    email: str | None = Field(default=None, max_length=320)
    whatsapp: str | None = Field(default=None, max_length=64)
    phone: str | None = Field(default=None, max_length=64)
    country: str | None = Field(default=None, max_length=128)
    language: str | None = Field(default=None, max_length=64)
    source_url: HttpUrl | None = None
    data_classification: str = Field(default="user_supplied", max_length=32)
    verification_status: str = Field(default="unverified", max_length=32)
    notes: str | None = None


class OutreachDraftCreate(BaseModel):
    contact_id: int | None = None
    product_id: int | None = None
    channel: str = Field(default="email", max_length=32)
    subject: str | None = Field(default=None, max_length=512)
    message_body: str | None = None
    negotiation_goal: str | None = Field(default=None, max_length=512)
    requested_terms: dict[str, Any] | None = None
    notes: str | None = None


class SupplierProductCreate(BaseModel):
    product_id: int | None = None
    supplier_product_url: HttpUrl | None = None
    supplier_product_name: str | None = Field(default=None, max_length=1024)
    purchase_cost: Decimal = Field(default=Decimal("0.0000"), ge=0)
    shipping_cost: Decimal = Field(default=Decimal("0.0000"), ge=0)
    processing_fee: Decimal = Field(default=Decimal("0.0000"), ge=0)
    currency_code: str = Field(default="USD", max_length=8)
    warehouse_origin: str | None = Field(default=None, max_length=256)
    warehouse_verified: bool = False
    warehouse_verification_status: str = Field(default="unverified", max_length=32)
    warehouse_verification_note: str | None = None
    stock_available: bool = False
    stock_quantity: str | None = Field(default=None, max_length=64)
    processing_time_days: int | None = Field(default=None, ge=0)
    delivery_estimate_days: int | None = Field(default=None, ge=0)
    shipping_service: str | None = Field(default=None, max_length=128)
    destination_zip: str | None = Field(default=None, max_length=16)
    evidence_status: str = Field(default="user_supplied", max_length=32)


@router.get("/list", response_model=list[dict[str, Any]])
async def list_suppliers(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
    search: str | None = Query(None),
    platform: str | None = Query(None),
    limit: int = Query(100, ge=1, le=300),
) -> list[dict[str, Any]]:
    query = select(Supplier).order_by(Supplier.created_at.desc())
    if search:
        like = f"%{search}%"
        query = query.where(or_(Supplier.name.ilike(like), Supplier.platform.ilike(like)))
    if platform:
        query = query.where(Supplier.platform == platform)
    result = await session.execute(query.limit(limit))
    return [_serialize_supplier(supplier) for supplier in result.scalars().all()]


@router.post("/create", response_model=dict[str, Any])
async def create_supplier(
    payload: SupplierCreate,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    existing = await session.execute(
        select(Supplier).where(Supplier.name == payload.name, Supplier.platform == payload.platform)
    )
    supplier = existing.scalar_one_or_none()
    if supplier is None:
        supplier = Supplier(
            name=payload.name,
            platform=payload.platform,
            website_url=str(payload.website_url) if payload.website_url else None,
            supports_shopify=payload.supports_shopify,
            supports_automation=payload.supports_automation,
            provides_tracking=payload.provides_tracking,
            supports_returns=payload.supports_returns,
            return_policy_note=payload.return_policy_note,
            us_warehouse_capable=payload.us_warehouse_capable,
            us_warehouse_note=payload.us_warehouse_note,
            reliability_status=payload.reliability_status,
            reliability_note=payload.reliability_note,
        )
        session.add(supplier)
        await session.commit()
        await session.refresh(supplier)
    return _serialize_supplier(supplier)


@router.get("/products/compare", response_model=dict[str, Any])
async def compare_supplier_products(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
    product_query: str | None = Query(None),
    limit: int = Query(100, ge=1, le=300),
) -> dict[str, Any]:
    query = select(SupplierProduct, Supplier).join(Supplier, Supplier.id == SupplierProduct.supplier_id)
    if product_query:
        like = f"%{product_query}%"
        query = query.where(SupplierProduct.supplier_product_name.ilike(like))
    result = await session.execute(query.limit(limit))
    rows = [
        _serialize_supplier_product(product, supplier)
        for product, supplier in result.all()
    ]
    ranked = sorted(rows, key=lambda row: (-row["recommendation_score"], row["total_landed_cost"]))
    return {
        "count": len(ranked),
        "recommended": ranked[0] if ranked else None,
        "products": ranked,
    }


@router.get("/{supplier_id}", response_model=dict[str, Any])
async def get_supplier(
    supplier_id: int,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    supplier = await _get_supplier_or_404(session, supplier_id)
    return _serialize_supplier(supplier, include_children=True)


@router.post("/{supplier_id}/products", response_model=dict[str, Any])
async def add_supplier_product(
    supplier_id: int,
    payload: SupplierProductCreate,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    supplier = await _get_supplier_or_404(session, supplier_id)
    supplier_product = SupplierProduct(
        supplier_id=supplier_id,
        product_id=payload.product_id,
        supplier_product_url=str(payload.supplier_product_url) if payload.supplier_product_url else None,
        supplier_product_name=payload.supplier_product_name,
        purchase_cost=payload.purchase_cost,
        shipping_cost=payload.shipping_cost,
        processing_fee=payload.processing_fee,
        currency_code=payload.currency_code.upper(),
        warehouse_origin=payload.warehouse_origin,
        warehouse_verified=payload.warehouse_verified,
        warehouse_verification_status=payload.warehouse_verification_status,
        warehouse_verification_note=payload.warehouse_verification_note,
        stock_available=payload.stock_available,
        stock_quantity=payload.stock_quantity,
        processing_time_days=payload.processing_time_days,
        delivery_estimate_days=payload.delivery_estimate_days,
        shipping_service=payload.shipping_service,
        destination_zip=payload.destination_zip,
        evidence_status=payload.evidence_status,
    )
    session.add(supplier_product)
    await session.commit()
    await session.refresh(supplier_product)
    return _serialize_supplier_product(supplier_product, supplier)


@router.post("/{supplier_id}/contacts", response_model=dict[str, Any])
async def add_supplier_contact(
    supplier_id: int,
    payload: SupplierContactCreate,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    await _get_supplier_or_404(session, supplier_id)
    contact = SupplierContact(
        supplier_id=supplier_id,
        contact_name=payload.contact_name,
        role_title=payload.role_title,
        email=payload.email,
        whatsapp=payload.whatsapp,
        phone=payload.phone,
        country=payload.country,
        language=payload.language,
        source_url=str(payload.source_url) if payload.source_url else None,
        data_classification=payload.data_classification,
        verification_status=payload.verification_status,
        notes=payload.notes,
    )
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return _serialize_contact(contact)


@router.post("/{supplier_id}/outreach/draft", response_model=dict[str, Any])
async def create_outreach_draft(
    supplier_id: int,
    payload: OutreachDraftCreate,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    supplier = await _get_supplier_or_404(session, supplier_id)
    subject = payload.subject or f"Product sourcing inquiry for {supplier.name}"
    message = payload.message_body or _default_outreach_message(supplier, payload.negotiation_goal)
    outreach = SupplierOutreach(
        supplier_id=supplier_id,
        contact_id=payload.contact_id,
        product_id=payload.product_id,
        channel=payload.channel,
        status="draft",
        subject=subject,
        message_body=message,
        negotiation_goal=payload.negotiation_goal,
        requested_terms_json=payload.requested_terms,
        notes=payload.notes,
    )
    session.add(outreach)
    await session.commit()
    await session.refresh(outreach)
    return _serialize_outreach(outreach)


async def _get_supplier_or_404(session: AsyncSession, supplier_id: int) -> Supplier:
    result = await session.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


def _default_outreach_message(supplier: Supplier, goal: str | None) -> str:
    goal_text = goal or "confirm product pricing, MOQ, warehouse availability, shipping time, and sample terms"
    return (
        f"Hello {supplier.name} team,\n\n"
        "I am researching products for Amazon and Shopify sales in the US market. "
        f"I would like to {goal_text}.\n\n"
        "Could you please share:\n"
        "1. Product catalog or exact product link\n"
        "2. Unit cost and MOQ\n"
        "3. Available warehouse locations\n"
        "4. Processing time and shipping options\n"
        "5. Return policy and warranty terms\n"
        "6. Best price for a sample order and for larger quantities\n\n"
        "Thank you."
    )


def _serialize_supplier(supplier: Supplier, include_children: bool = False) -> dict[str, Any]:
    data = {
        "id": supplier.id,
        "name": supplier.name,
        "platform": supplier.platform,
        "website_url": supplier.website_url,
        "supports_shopify": supplier.supports_shopify,
        "supports_automation": supplier.supports_automation,
        "provides_tracking": supplier.provides_tracking,
        "supports_returns": supplier.supports_returns,
        "return_policy_note": supplier.return_policy_note,
        "us_warehouse_capable": supplier.us_warehouse_capable,
        "us_warehouse_note": supplier.us_warehouse_note,
        "reliability_status": supplier.reliability_status,
        "reliability_note": supplier.reliability_note,
        "contact_count": len(supplier.contacts or []),
        "outreach_count": len(supplier.outreach_messages or []),
        "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
    }
    if include_children:
        data["contacts"] = [_serialize_contact(contact) for contact in (supplier.contacts or [])]
        data["outreach"] = [_serialize_outreach(outreach) for outreach in (supplier.outreach_messages or [])]
        data["supplier_products"] = [
            _serialize_supplier_product(product, supplier)
            for product in (supplier.supplier_products or [])
        ]
    return data


def _serialize_contact(contact: SupplierContact) -> dict[str, Any]:
    return {
        "id": contact.id,
        "supplier_id": contact.supplier_id,
        "contact_name": contact.contact_name,
        "role_title": contact.role_title,
        "email": contact.email,
        "whatsapp": contact.whatsapp,
        "phone": contact.phone,
        "country": contact.country,
        "language": contact.language,
        "source_url": contact.source_url,
        "data_classification": contact.data_classification,
        "verification_status": contact.verification_status,
        "notes": contact.notes,
        "created_at": contact.created_at.isoformat() if contact.created_at else None,
    }


def _serialize_outreach(outreach: SupplierOutreach) -> dict[str, Any]:
    return {
        "id": outreach.id,
        "supplier_id": outreach.supplier_id,
        "contact_id": outreach.contact_id,
        "product_id": outreach.product_id,
        "channel": outreach.channel,
        "status": outreach.status,
        "subject": outreach.subject,
        "message_body": outreach.message_body,
        "negotiation_goal": outreach.negotiation_goal,
        "requested_terms": outreach.requested_terms_json,
        "sent_at": outreach.sent_at.isoformat() if outreach.sent_at else None,
        "external_message_id": outreach.external_message_id,
        "notes": outreach.notes,
        "created_at": outreach.created_at.isoformat() if outreach.created_at else None,
    }


def _serialize_supplier_product(product: SupplierProduct, supplier: Supplier | None = None) -> dict[str, Any]:
    total_landed_cost = product.purchase_cost + product.shipping_cost + product.processing_fee
    score, reasons = _supplier_product_score(product, supplier, total_landed_cost)
    return {
        "id": product.id,
        "supplier_id": product.supplier_id,
        "supplier_name": supplier.name if supplier else None,
        "supplier_platform": supplier.platform if supplier else None,
        "product_id": product.product_id,
        "supplier_product_url": product.supplier_product_url,
        "supplier_product_name": product.supplier_product_name,
        "purchase_cost": float(product.purchase_cost),
        "shipping_cost": float(product.shipping_cost),
        "processing_fee": float(product.processing_fee),
        "total_landed_cost": float(total_landed_cost),
        "currency_code": product.currency_code,
        "warehouse_origin": product.warehouse_origin,
        "warehouse_verified": product.warehouse_verified,
        "warehouse_verification_status": product.warehouse_verification_status,
        "stock_available": product.stock_available,
        "stock_quantity": product.stock_quantity,
        "processing_time_days": product.processing_time_days,
        "delivery_estimate_days": product.delivery_estimate_days,
        "shipping_service": product.shipping_service,
        "destination_zip": product.destination_zip,
        "evidence_status": product.evidence_status,
        "recommendation_score": score,
        "recommendation_reasons": reasons,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }


def _supplier_product_score(
    product: SupplierProduct,
    supplier: Supplier | None,
    total_landed_cost: Decimal,
) -> tuple[int, list[str]]:
    score = 50
    reasons: list[str] = []

    if product.stock_available:
        score += 15
        reasons.append("Stock available")
    if product.warehouse_verified:
        score += 15
        reasons.append("Warehouse verified")
    if supplier and supplier.supports_shopify:
        score += 6
        reasons.append("Shopify capable")
    if supplier and supplier.provides_tracking:
        score += 5
        reasons.append("Tracking supported")
    if supplier and supplier.supports_returns:
        score += 4
        reasons.append("Returns supported")
    if product.delivery_estimate_days is not None:
        if product.delivery_estimate_days <= 7:
            score += 10
            reasons.append("Fast delivery")
        elif product.delivery_estimate_days <= 14:
            score += 5
            reasons.append("Acceptable delivery")
        else:
            score -= 5
            reasons.append("Long delivery estimate")
    if total_landed_cost <= Decimal("5"):
        score += 8
        reasons.append("Low landed cost")
    elif total_landed_cost >= Decimal("30"):
        score -= 8
        reasons.append("High landed cost")
    if product.evidence_status in {"verified", "user_supplied"}:
        score += 5
        reasons.append("Evidence recorded")
    if supplier and supplier.reliability_status in {"verified", "approved", "reliable"}:
        score += 8
        reasons.append("Supplier reliability marked")

    return max(0, min(score, 100)), reasons
