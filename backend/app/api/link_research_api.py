from __future__ import annotations

import json
import re
from decimal import Decimal
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers import AIORchestrator
from app.api.deps import get_ai_orchestrator, require_access_token
from app.database import get_db
from app.models.core import utc_now
from app.models.product import Product, ProductSource, Region
from app.models.supplier import Supplier, SupplierProduct
from app.services.financial import CostComponents, calculate_financials

router = APIRouter(prefix="/link-research", tags=["link-research"])


class SupplierLinkResearchCreate(BaseModel):
    mode: str = Field(default="create", max_length=32)
    existing_product_id: int | None = None

    url: str = Field(max_length=2048)
    goal_prompt: str | None = Field(default=None, max_length=4096)
    product_name: str | None = Field(default=None, max_length=512)
    category: str | None = Field(default=None, max_length=128)
    supplier_name: str | None = Field(default=None, max_length=256)
    supplier_platform: str = Field(default="manual_entry", max_length=128)
    supplier_cost: Decimal = Field(default=Decimal("0.0000"), ge=0)
    shipping_cost: Decimal = Field(default=Decimal("0.0000"), ge=0)
    processing_fee: Decimal = Field(default=Decimal("0.0000"), ge=0)
    suggested_retail_price: Decimal = Field(default=Decimal("0.0000"), ge=0)
    inventory_quantity: str | None = Field(default=None, max_length=64)
    warehouse_origin: str | None = Field(default=None, max_length=256)
    delivery_estimate_days: int | None = Field(default=None, ge=0)
    processing_time_days: int | None = Field(default=None, ge=0)
    shipping_service: str | None = Field(default=None, max_length=128)
    supplier_contact: str | None = Field(default=None, max_length=256)
    return_policy_note: str | None = Field(default=None, max_length=1024)
    notes: str | None = Field(default=None, max_length=4096)


class LinkResearchRequest(BaseModel):
    url: str = Field(max_length=2048)
    page_text: str | None = None
    product_name: str | None = Field(default=None, max_length=512)
    category: str | None = Field(default=None, max_length=128)
    supplier_cost: Decimal = Field(default=Decimal("0.0000"), ge=0)
    shipping_cost: Decimal = Field(default=Decimal("0.0000"), ge=0)
    suggested_retail_price: Decimal = Field(default=Decimal("0.0000"), ge=0)
    target_marketplace: str = Field(default="both", max_length=32)
    save_product: bool = True


@router.post("/analyze", response_model=dict[str, Any])


@router.post("/analyze-guided", response_model=dict[str, Any])
async def analyze_link_guided(
    payload: SupplierLinkResearchCreate,
    session: AsyncSession = Depends(get_db),
    orchestrator: AIORchestrator = Depends(get_ai_orchestrator),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    inferred_name = payload.product_name or _name_from_url(payload.url)
    financials = calculate_financials(
        payload.suggested_retail_price,
        CostComponents(
            purchase_cost=payload.supplier_cost,
            shipping_cost=payload.shipping_cost,
            payment_processing_rate=Decimal("0.029"),
            payment_processing_fixed=Decimal("0.30"),
            marketplace_fee_rate=Decimal("0.00"),
            expected_return_rate=Decimal("0.05"),
        ),
    )
    deterministic = _deterministic_recommendation(financials.contribution_margin_after_advertising)
    ai_status = orchestrator.status()
    evidence_text = _build_guided_evidence_text(payload, inferred_name, financials.to_dict())
    ai_analysis = None
    if orchestrator.is_configured:
        ai_analysis = await _ai_product_verdict(orchestrator, payload.url, inferred_name, payload.goal_prompt or "", evidence_text)
    verdict = _build_product_verdict(
        deterministic=deterministic,
        financials=financials.to_dict(),
        ai_analysis=ai_analysis,
        ai_configured=ai_status["configured"],
        payload=payload,
    )

    region = await _get_or_create_region(session)
    product_id = None
    supplier_id = None
    supplier_product_id = None

    if payload.mode == "create":
        product = Product(
            region_id=region.id,
            name=inferred_name,
            description=payload.notes,
            category=payload.category,
            product_url=payload.url,
            supplier_cost=payload.supplier_cost,
            shipping_cost=payload.shipping_cost,
            packaging_cost=payload.processing_fee,
            suggested_retail_price=payload.suggested_retail_price,
            trend_classification="needs_review",
            viral_potential="unknown",
            primary_competition_level="unknown",
            status="candidate",
        )
        session.add(product)
        await session.flush()
        product_id = product.id

        source = ProductSource(
            product_id=product.id,
            source_name="free_link_research_guided",
            source_type="supplier_or_product_page",
            source_url=payload.url,
            retrieval_timestamp=utc_now(),
            raw_value=(payload.notes or "")[:8000],
            data_classification="user_supplied",
            notes="Manual guided form entry",
        )
        session.add(source)

        if payload.supplier_name:
            supplier = await session.execute(
                select(Supplier).where(
                    Supplier.name == payload.supplier_name,
                    Supplier.platform == payload.supplier_platform,
                )
            )
            supplier = supplier.scalar_one_or_none()
            if supplier is None:
                us_warehouse_capable = bool(
                    payload.warehouse_origin
                    and payload.warehouse_origin.lower() not in {"china", "cn", "canton"}
                )
                supplier = Supplier(
                    name=payload.supplier_name,
                    platform=payload.supplier_platform,
                    website_url=payload.url,
                    supports_shopify=False,
                    supports_automation=False,
                    provides_tracking=False,
                    supports_returns=bool(payload.return_policy_note),
                    return_policy_note=payload.return_policy_note,
                    us_warehouse_capable=us_warehouse_capable,
                    us_warehouse_note=payload.warehouse_origin if us_warehouse_capable else None,
                    reliability_status="unassessed",
                )
                session.add(supplier)
                await session.flush()
                supplier_id = supplier.id
            else:
                supplier_id = supplier.id

            existing = await session.execute(
                select(SupplierProduct).where(
                    SupplierProduct.supplier_id == supplier.id,
                    SupplierProduct.supplier_product_url == payload.url,
                )
            )
            match = existing.scalar_one_or_none()
            if match is None:
                sp = SupplierProduct(
                    supplier_id=supplier.id,
                    product_id=product_id,
                    supplier_product_url=payload.url,
                    supplier_product_name=payload.product_name or inferred_name,
                    purchase_cost=payload.supplier_cost,
                    shipping_cost=payload.shipping_cost,
                    processing_fee=payload.processing_fee,
                    currency_code="USD",
                    warehouse_origin=payload.warehouse_origin,
                    warehouse_verified=False,
                    warehouse_verification_status="unverified",
                    stock_available=bool(payload.inventory_quantity),
                    stock_quantity=payload.inventory_quantity,
                    processing_time_days=payload.processing_time_days,
                    delivery_estimate_days=payload.delivery_estimate_days,
                    shipping_service=payload.shipping_service,
                    destination_zip=None,
                    evidence_status="user_supplied",
                    verification_timestamp=utc_now(),
                )
                session.add(sp)
                await session.flush()
                supplier_product_id = sp.id
            else:
                supplier_product_id = match.id

        await session.commit()
        contact_note = (
            f"Supplier contact: {payload.supplier_contact}" if payload.supplier_contact else ""
        )
        notes = " ".join([n for n in [contact_note, payload.notes] if n])
        source = await session.execute(
            select(ProductSource).where(ProductSource.product_id == product_id)
        )
        source = source.scalar_one()
        source.notes = notes or source.notes
        await session.commit()

        return {
            "product_id": product_id,
            "name": inferred_name,
            "url": payload.url,
            "mode": "create",
            "supplier_id": supplier_id,
            "supplier_product_id": supplier_product_id,
            "fetch_status": "not_attempted",
            "ai": {"configured": ai_status["configured"], "provider": ai_status["provider"], "analysis": ai_analysis},
            "financials": financials.to_dict(),
            "recommendation": verdict,
            "note": "Saved product and supplier evidence from guided form.",
        }

    if payload.mode == "update" and payload.existing_product_id:
        result = await session.execute(select(Product).where(Product.id == payload.existing_product_id))
        product = result.scalar_one_or_none()
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        product.name = payload.product_name or product.name
        product.category = payload.category or product.category
        product.product_url = payload.url or product.product_url
        product.supplier_cost = payload.supplier_cost
        product.shipping_cost = payload.shipping_cost
        product.packaging_cost = payload.processing_fee
        product.suggested_retail_price = payload.suggested_retail_price
        if payload.notes:
            existing_notes = product.description or ""
            combined = " ".join([n for n in [existing_notes, payload.notes] if n])
            product.description = combined.strip()
        await session.flush()

        source = ProductSource(
            product_id=product.id,
            source_name="free_link_research_guided",
            source_type="supplier_or_product_page",
            source_url=payload.url,
            retrieval_timestamp=utc_now(),
            raw_value=(payload.notes or "")[:8000],
            data_classification="user_supplied",
            notes="Updated from guided form",
        )
        session.add(source)

        supplier_id_out = None
        supplier_product_id_out = None
        if payload.supplier_name:
            supplier = await session.execute(
                select(Supplier).where(
                    Supplier.name == payload.supplier_name,
                    Supplier.platform == payload.supplier_platform,
                )
            )
            supplier = supplier.scalar_one_or_none()
            if supplier is None:
                us_warehouse_capable = bool(
                    payload.warehouse_origin
                    and payload.warehouse_origin.lower() not in {"china", "cn", "canton"}
                )
                supplier = Supplier(
                    name=payload.supplier_name,
                    platform=payload.supplier_platform,
                    website_url=payload.url,
                    supports_shopify=False,
                    supports_automation=False,
                    provides_tracking=False,
                    supports_returns=bool(payload.return_policy_note),
                    return_policy_note=payload.return_policy_note,
                    us_warehouse_capable=us_warehouse_capable,
                    us_warehouse_note=payload.warehouse_origin if us_warehouse_capable else None,
                    reliability_status="unassessed",
                )
                session.add(supplier)
                await session.flush()
                supplier_id_out = supplier.id
            else:
                supplier_id_out = supplier.id

            existing = await session.execute(
                select(SupplierProduct).where(
                    SupplierProduct.supplier_id == supplier.id,
                    SupplierProduct.product_id == product.id,
                )
            )
            match = existing.scalar_one_or_none()
            if match is not None:
                match.supplier_product_url = payload.url
                match.supplier_product_name = payload.product_name or product.name
                match.purchase_cost = payload.supplier_cost
                match.shipping_cost = payload.shipping_cost
                match.processing_fee = payload.processing_fee
                match.warehouse_origin = payload.warehouse_origin
                match.warehouse_verified = False
                match.warehouse_verification_status = "unverified"
                match.stock_available = bool(payload.inventory_quantity)
                match.stock_quantity = payload.inventory_quantity
                match.processing_time_days = payload.processing_time_days
                match.delivery_estimate_days = payload.delivery_estimate_days
                match.shipping_service = payload.shipping_service
                match.evidence_status = "user_supplied"
                match.verification_timestamp = utc_now()
                supplier_product_id_out = match.id
            else:
                sp = SupplierProduct(
                    supplier_id=supplier.id,
                    product_id=product.id,
                    supplier_product_url=payload.url,
                    supplier_product_name=payload.product_name or product.name,
                    purchase_cost=payload.supplier_cost,
                    shipping_cost=payload.shipping_cost,
                    processing_fee=payload.processing_fee,
                    currency_code="USD",
                    warehouse_origin=payload.warehouse_origin,
                    warehouse_verified=False,
                    warehouse_verification_status="unverified",
                    stock_available=bool(payload.inventory_quantity),
                    stock_quantity=payload.inventory_quantity,
                    processing_time_days=payload.processing_time_days,
                    delivery_estimate_days=payload.delivery_estimate_days,
                    shipping_service=payload.shipping_service,
                    destination_zip=None,
                    evidence_status="user_supplied",
                    verification_timestamp=utc_now(),
                )
                session.add(sp)
                await session.flush()
                supplier_product_id_out = sp.id

        await session.commit()

        return {
            "product_id": product.id,
            "name": product.name,
            "url": product.product_url or payload.url,
            "mode": "update",
            "supplier_id": supplier_id_out,
            "supplier_product_id": supplier_product_id_out,
            "fetch_status": "not_attempted",
            "ai": {"configured": ai_status["configured"], "provider": ai_status["provider"], "analysis": ai_analysis},
            "financials": financials.to_dict(),
            "recommendation": verdict,
            "note": "Updated existing product and supplier evidence from guided form.",
        }

    raise HTTPException(status_code=400, detail="Unsupported mode")


async def analyze_link(
    payload: LinkResearchRequest,
    session: AsyncSession = Depends(get_db),
    orchestrator: AIORchestrator = Depends(AIORchestrator),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    return await _analyze_link_common(payload, session, orchestrator)


async def _analyze_link_common(
    payload: LinkResearchRequest,
    session: AsyncSession,
    orchestrator: AIORchestrator,
) -> dict[str, Any]:
    fetched_text = ""
    fetch_status = "not_attempted"
    if not payload.page_text:
        fetched_text, fetch_status = await _fetch_public_page_text(payload.url)

    evidence_text = (payload.page_text or fetched_text or "")[:12000]
    inferred_name = payload.product_name or _extract_title(evidence_text) or _name_from_url(payload.url)
    financials = calculate_financials(
        payload.suggested_retail_price,
        CostComponents(
            purchase_cost=payload.supplier_cost,
            shipping_cost=payload.shipping_cost,
            payment_processing_rate=Decimal("0.029"),
            payment_processing_fixed=Decimal("0.30"),
            marketplace_fee_rate=Decimal("0.15") if payload.target_marketplace == "amazon" else Decimal("0.00"),
            expected_return_rate=Decimal("0.05"),
        ),
    )

    deterministic = _deterministic_recommendation(financials.contribution_margin_after_advertising)
    ai_analysis = None
    ai_status = orchestrator.status()
    if orchestrator.is_configured and evidence_text:
        ai_analysis = await _ai_link_analysis(orchestrator, payload.url, inferred_name, evidence_text)

    product_id = None
    if payload.save_product:
        region = await _get_or_create_region(session)
        product = Product(
            region_id=region.id,
            name=inferred_name,
            description=(ai_analysis or {}).get("summary") if ai_analysis else None,
            category=payload.category,
            product_url=payload.url,
            supplier_cost=payload.supplier_cost,
            shipping_cost=payload.shipping_cost,
            suggested_retail_price=payload.suggested_retail_price,
            trend_classification=(ai_analysis or {}).get("trend_classification", "needs_review"),
            viral_potential=(ai_analysis or {}).get("viral_potential", "unknown"),
            primary_competition_level=(ai_analysis or {}).get("competition_level", "unknown"),
            status="candidate",
        )
        session.add(product)
        await session.flush()
        source = ProductSource(
            product_id=product.id,
            source_name="free_link_research",
            source_type="supplier_or_product_page",
            source_url=payload.url,
            retrieval_timestamp=utc_now(),
            raw_value=evidence_text[:8000],
            data_classification="user_supplied" if payload.page_text else "public_page_fetch",
            notes=f"Fetch status: {fetch_status}",
        )
        session.add(source)
        await session.commit()
        product_id = product.id

    return {
        "product_id": product_id,
        "name": inferred_name,
        "url": payload.url,
        "fetch_status": fetch_status,
        "ai": {"configured": ai_status["configured"], "provider": ai_status["provider"], "analysis": ai_analysis},
        "financials": financials.to_dict(),
        "recommendation": deterministic,
        "note": "Use pasted page text from your browser when a site blocks automatic public page fetching.",
    }


async def _fetch_public_page_text(url: str) -> tuple[str, str]:
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "ProductHunterAI/0.1 local research"})
            response.raise_for_status()
            text = re.sub(r"<script[\s\S]*?</script>", " ", response.text, flags=re.IGNORECASE)
            text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:20000], "fetched"
    except Exception as exc:
        return "", f"blocked_or_failed: {exc.__class__.__name__}"


async def _ai_link_analysis(
    orchestrator: AIORchestrator,
    url: str,
    name: str,
    evidence_text: str,
) -> dict[str, Any] | None:
    prompt = (
        "Analyze this product/supplier page for ecommerce opportunity. Return only JSON with keys: "
        "summary, trend_classification, viral_potential, competition_level, risks, supplier_questions, "
        "recommended_next_steps. Do not invent prices or sales data.\n\n"
        f"URL: {url}\nProduct name: {name}\nPage evidence:\n{evidence_text[:10000]}"
    )
    try:
        text = await orchestrator.chat_completion([{"role": "user", "content": prompt}], temperature=0.2, max_tokens=1200)
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except Exception as exc:
        return {"summary": "AI analysis failed; deterministic profitability analysis is still available.", "error": str(exc)}


def _build_guided_evidence_text(payload: SupplierLinkResearchCreate, inferred_name: str, financials: dict[str, Any]) -> str:
    parts = [
        f"User goal: {payload.goal_prompt or 'Find and verify whether this is a good ecommerce product.'}",
        f"URL: {payload.url}",
        f"Product name: {inferred_name}",
        f"Category: {payload.category or 'unknown'}",
        f"Supplier: {payload.supplier_name or 'unknown'} on {payload.supplier_platform}",
        f"Supplier cost: {payload.supplier_cost}",
        f"Shipping cost: {payload.shipping_cost}",
        f"Processing fee: {payload.processing_fee}",
        f"Suggested selling price: {payload.suggested_retail_price}",
        f"Warehouse origin: {payload.warehouse_origin or 'unknown'}",
        f"Delivery estimate days: {payload.delivery_estimate_days if payload.delivery_estimate_days is not None else 'unknown'}",
        f"Processing time days: {payload.processing_time_days if payload.processing_time_days is not None else 'unknown'}",
        f"Shipping service: {payload.shipping_service or 'unknown'}",
        f"Inventory quantity: {payload.inventory_quantity or 'unknown'}",
        f"Return policy: {payload.return_policy_note or 'unknown'}",
        f"Financial calculation: {json.dumps(financials, default=str)}",
        f"User pasted page notes: {payload.notes or ''}",
    ]
    return "\n".join(parts)


async def _ai_product_verdict(
    orchestrator: AIORchestrator,
    url: str,
    name: str,
    goal_prompt: str,
    evidence_text: str,
) -> dict[str, Any] | None:
    prompt = (
        "You are a practical ecommerce product research assistant. The user wants help choosing products to sell.\n"
        "Analyze the supplied link evidence and return only JSON. Do not invent sales data, supplier stock, reviews, "
        "competitor counts, delivery promises, or prices. If evidence is missing, mark it missing.\n\n"
        f"URL: {url}\nProduct name: {name}\nUser goal:\n{goal_prompt or 'Verify whether this product is worth working on.'}\n\n"
        f"Evidence:\n{evidence_text[:12000]}\n\n"
        "Return JSON with this shape:\n"
        "{\n"
        '  "decision": "work_on_it" | "shortlist" | "avoid" | "needs_more_proof",\n'
        '  "confidence": "high" | "medium" | "low",\n'
        '  "plain_verdict": "one direct sentence",\n'
        '  "why": ["reason", "reason"],\n'
        '  "risks": ["risk", "risk"],\n'
        '  "missing_proof": ["proof needed"],\n'
        '  "next_steps": ["specific next step"],\n'
        '  "supplier_questions": ["question to ask supplier"],\n'
        '  "positioning_angle": "how to differentiate it if promising"\n'
        "}"
    )
    try:
        text = await orchestrator.chat_completion([{"role": "user", "content": prompt}], temperature=0.2, max_tokens=1600)
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except Exception as exc:
        return {
            "decision": "needs_more_proof",
            "confidence": "low",
            "plain_verdict": "AI analysis failed, so only deterministic profitability checks are available.",
            "why": [],
            "risks": [str(exc)],
            "missing_proof": ["AI provider response"],
            "next_steps": ["Retry after checking AI settings, or review manually."],
            "supplier_questions": [],
            "positioning_angle": "",
        }


async def _get_or_create_region(session: AsyncSession) -> Region:
    result = await session.execute(select(Region).where(Region.code == "US"))
    region = result.scalar_one_or_none()
    if region:
        return region
    region = Region(code="US", name="United States", currency_code="USD", default_language="en", is_primary=True)
    session.add(region)
    await session.flush()
    return region


def _extract_title(text: str) -> str | None:
    if not text:
        return None
    for line in text.splitlines():
        stripped = line.strip()
        if 8 <= len(stripped) <= 120:
            return stripped
    return None


def _name_from_url(url: str) -> str:
    slug = url.rstrip("/").split("/")[-1].split("?")[0]
    name = re.sub(r"[-_]+", " ", slug).strip()
    return name.title() if name else "Imported Link Product"


def _deterministic_recommendation(margin_percent: Decimal) -> dict[str, Any]:
    if margin_percent >= Decimal("35"):
        return {"rating": "strong", "reason": "Estimated contribution margin is attractive based on entered costs."}
    if margin_percent >= Decimal("20"):
        return {"rating": "review", "reason": "Margin is possible, but supplier terms and competition need checking."}
    return {"rating": "weak", "reason": "Estimated margin is low based on entered costs."}


def _build_product_verdict(
    deterministic: dict[str, Any],
    financials: dict[str, Any],
    ai_analysis: dict[str, Any] | None,
    ai_configured: bool,
    payload: SupplierLinkResearchCreate,
) -> dict[str, Any]:
    if ai_analysis and ai_analysis.get("decision"):
        rating_map = {
            "work_on_it": "strong",
            "shortlist": "review",
            "needs_more_proof": "review",
            "avoid": "weak",
        }
        return {
            "rating": rating_map.get(str(ai_analysis.get("decision")), deterministic["rating"]),
            "reason": ai_analysis.get("plain_verdict") or deterministic["reason"],
            "decision": ai_analysis.get("decision"),
            "confidence": ai_analysis.get("confidence", "low"),
            "why": ai_analysis.get("why", []),
            "risks": ai_analysis.get("risks", []),
            "missing_proof": ai_analysis.get("missing_proof", []),
            "next_steps": ai_analysis.get("next_steps", []),
            "supplier_questions": ai_analysis.get("supplier_questions", []),
            "positioning_angle": ai_analysis.get("positioning_angle", ""),
        }

    missing_proof = []
    if not payload.supplier_name:
        missing_proof.append("Supplier identity")
    if payload.supplier_cost == 0:
        missing_proof.append("Supplier product cost")
    if payload.suggested_retail_price == 0:
        missing_proof.append("Target selling price")
    if not payload.delivery_estimate_days:
        missing_proof.append("Delivery time")
    if not payload.notes:
        missing_proof.append("Copied page evidence, competitor notes, or demand proof")
    if not ai_configured:
        missing_proof.append("AI provider is not configured, so this is a rule-based verdict")

    decision = "shortlist" if deterministic["rating"] == "strong" and len(missing_proof) <= 2 else "needs_more_proof"
    if deterministic["rating"] == "weak":
        decision = "avoid"

    return {
        "rating": deterministic["rating"],
        "reason": deterministic["reason"],
        "decision": decision,
        "confidence": "medium" if not missing_proof else "low",
        "why": [
            f"Estimated contribution margin after advertising is {financials.get('contribution_margin_after_advertising')}%.",
            "The result is based only on data entered or pasted into this form.",
        ],
        "risks": [
            "Demand, competition, reviews, supplier reliability, and delivery promise are not verified automatically.",
        ],
        "missing_proof": missing_proof,
        "next_steps": [
            "Verify supplier stock, MOQ, and delivery time.",
            "Search Amazon, TikTok, and Google for competing versions of the same product.",
            "Ask the supplier for real product photos, shipping quote, and return policy.",
        ],
        "supplier_questions": [
            "What is the exact unit cost at 10, 50, and 100 units?",
            "Which country does the item ship from and what is the real delivery time?",
            "Can you provide tracking, returns support, and product compliance documents if needed?",
        ],
        "positioning_angle": "Not enough verified evidence yet. Look for a specific buyer problem and differentiation angle.",
    }
