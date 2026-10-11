from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import load_only, noload, selectinload

from app.database import get_db
from app.models.product import Product, ProductVariant, ProductSource, WatchlistStatus, Region
from app.models.supplier import Supplier, SupplierProduct
from app.models.research import OpportunityScore, FinancialScenario, MarketObservation, SocialMediaObservation, Competitor
from app.models.core import utc_now
from app.api.deps import require_access_token
from app.services.financial import CostComponents, calculate_financials, build_sensitivity_table

router = APIRouter(prefix="/products", tags=["products"])


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=512)
    description: str | None = None
    category: str | None = Field(default=None, max_length=128)
    brand: str | None = Field(default=None, max_length=256)
    product_url: HttpUrl | None = None
    image_url: HttpUrl | None = None
    supplier_cost: Decimal = Field(default=Decimal("0.0000"), ge=0)
    shipping_cost: Decimal = Field(default=Decimal("0.0000"), ge=0)
    packaging_cost: Decimal = Field(default=Decimal("0.0000"), ge=0)
    other_landed_cost: Decimal = Field(default=Decimal("0.0000"), ge=0)
    suggested_retail_price: Decimal = Field(default=Decimal("0.0000"), ge=0)
    trend_classification: str = Field(default="insufficient_evidence", max_length=32)
    viral_potential: str = Field(default="low", max_length=16)
    primary_competition_level: str = Field(default="unknown", max_length=16)
    status: str = Field(default="candidate", max_length=32)
    region_code: str = Field(default="US", max_length=16)


@router.get("/list", response_model=list[dict[str, Any]])
async def list_products(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
    search: str | None = Query(None, min_length=1),
    category: str | None = None,
    status: str | None = None,
    region_code: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[dict[str, Any]]:
    query = (
        select(Product)
        .options(
            load_only(
                Product.id,
                Product.name,
                Product.category,
                Product.brand,
                Product.asin,
                Product.product_url,
                Product.image_url,
                Product.thumbnail_url,
                Product.supplier_cost,
                Product.shipping_cost,
                Product.suggested_retail_price,
                Product.us_warehouse_verified,
                Product.us_warehouse_verification_status,
                Product.trend_classification,
                Product.viral_potential,
                Product.primary_competition_level,
                Product.status,
                Product.created_at,
            ),
            selectinload(Product.region).load_only(Region.code),
            noload(Product.variants),
            noload(Product.sources),
            noload(Product.supplier_products),
            noload(Product.scores),
        )
        .order_by(Product.created_at.desc())
    )
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))
    if category:
        query = query.where(Product.category == category)
    if status:
        query = query.where(Product.status == status)
    if region_code:
        query = query.join(Region).where(Region.code == region_code)
    result = await session.execute(query.limit(limit).offset(offset))
    products = result.scalars().all()
    out: list[dict[str, Any]] = []
    for product in products:
        out.append(_serialize_product_basic(product))
    return out


@router.post("/create", response_model=dict[str, Any])
async def create_product(
    payload: ProductCreate,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    region_result = await session.execute(select(Region).where(Region.code == payload.region_code))
    region = region_result.scalar_one_or_none()
    if region is None:
        region = Region(
            code=payload.region_code,
            name=payload.region_code,
            currency_code="USD",
            default_language="en",
            is_primary=False,
        )
        session.add(region)
        await session.flush()

    product = Product(
        region_id=region.id,
        name=payload.name,
        description=payload.description,
        category=payload.category,
        brand=payload.brand,
        product_url=str(payload.product_url) if payload.product_url else None,
        image_url=str(payload.image_url) if payload.image_url else None,
        thumbnail_url=str(payload.image_url) if payload.image_url else None,
        supplier_cost=payload.supplier_cost,
        shipping_cost=payload.shipping_cost,
        packaging_cost=payload.packaging_cost,
        other_landed_cost=payload.other_landed_cost,
        suggested_retail_price=payload.suggested_retail_price,
        trend_classification=payload.trend_classification,
        viral_potential=payload.viral_potential,
        primary_competition_level=payload.primary_competition_level,
        status=payload.status,
    )
    session.add(product)
    await session.commit()
    await session.refresh(product)
    product.region = region
    return _serialize_product_basic(product)


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


@router.get("/detail/{product_id}", response_model=dict[str, Any])
async def product_detail(
    product_id: int,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return await _serialize_product_detail(product, session)


async def _serialize_product_detail(product: Product, session: AsyncSession | None = None) -> dict[str, Any]:
    shopify_score = None
    amazon_score = None
    if session is not None:
        scores = {}
        for score in (product.scores or []):
            scores[score.marketplace] = score
        shopify_score = scores.get("shopify")
        amazon_score = scores.get("amazon")

    suppliers = []
    if session is not None:
        sp_result = await session.execute(
            select(SupplierProduct).where(SupplierProduct.product_id == product.id)
        )
        for sp in sp_result.scalars().all():
            suppliers.append(_serialize_supplier(sp))

    scenarios = []
    if session is not None:
        sc_result = await session.execute(
            select(FinancialScenario).where(FinancialScenario.product_id == product.id)
        )
        scenarios = [_serialize_scenario(s) for s in sc_result.scalars().all()]

    observations = []
    if session is not None:
        obs_result = await session.execute(
            select(MarketObservation).where(MarketObservation.product_id == product.id)
        )
        observations = [_serialize_observation(o) for o in obs_result.scalars().all()]

    social = []
    if session is not None:
        soc_result = await session.execute(
            select(SocialMediaObservation).where(SocialMediaObservation.product_id == product.id)
        )
        social = [_serialize_social(o) for o in soc_result.scalars().all()]

    competitors = []
    if session is not None:
        comp_result = await session.execute(
            select(Competitor).where(Competitor.product_id == product.id)
        )
        competitors = [_serialize_competitor(c) for c in comp_result.scalars().all()]

    sources = []
    if session is not None:
        src_result = await session.execute(
            select(ProductSource).where(ProductSource.product_id == product.id)
        )
        sources = [_serialize_source(s) for s in src_result.scalars().all()]

    return {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "category": product.category,
        "brand": product.brand,
        "asin": product.asin,
        "upc": product.upc,
        "ean": product.ean,
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
        "shopify_score": shopify_score.total_score if shopify_score else None,
        "shopify_confidence": shopify_score.confidence_score if shopify_score else None,
        "shopify_components": shopify_score.component_scores_json if shopify_score else None,
        "shopify_weights": shopify_score.weights_json if shopify_score else None,
        "shopify_missing_fields": shopify_score.missing_fields_json if shopify_score else None,
        "amazon_score": amazon_score.total_score if amazon_score else None,
        "amazon_confidence": amazon_score.confidence_score if amazon_score else None,
        "amazon_components": amazon_score.component_scores_json if amazon_score else None,
        "amazon_weights": amazon_score.weights_json if amazon_score else None,
        "amazon_missing_fields": amazon_score.missing_fields_json if amazon_score else None,
        "scenarios": scenarios,
        "sources": sources,
        "suppliers": suppliers,
        "observations": observations,
        "social": social,
        "competitors": competitors,
        "variants": [_serialize_variant(v) for v in (product.variants or [])],
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


def _serialize_variant(v: ProductVariant) -> dict[str, Any]:
    return {
        "id": v.id,
        "sku": v.sku,
        "name": v.name,
        "attributes": v.attributes,
        "supplier_cost": str(v.supplier_cost),
        "shipping_cost": str(v.shipping_cost),
        "is_active": v.is_active,
    }


def _serialize_supplier(sp: SupplierProduct) -> dict[str, Any]:
    supplier = sp.supplier
    return {
        "id": sp.id,
        "supplier_name": supplier.name if supplier else None,
        "supplier_platform": supplier.platform if supplier else None,
        "supplier_url": supplier.website_url if supplier else None,
        "supplier_product_url": sp.supplier_product_url,
        "supplier_product_name": sp.supplier_product_name,
        "purchase_cost": str(sp.purchase_cost),
        "shipping_cost": str(sp.shipping_cost),
        "processing_fee": str(sp.processing_fee),
        "currency_code": sp.currency_code,
        "warehouse_origin": sp.warehouse_origin,
        "warehouse_verified": sp.warehouse_verified,
        "warehouse_verification_status": sp.warehouse_verification_status,
        "warehouse_verification_note": sp.warehouse_verification_note,
        "stock_available": sp.stock_available,
        "stock_quantity": sp.stock_quantity,
        "processing_time_days": sp.processing_time_days,
        "delivery_estimate_days": sp.delivery_estimate_days,
        "shipping_service": sp.shipping_service,
        "destination_zip": sp.destination_zip,
        "evidence_status": sp.evidence_status,
        "verification_timestamp": sp.verification_timestamp.isoformat() if sp.verification_timestamp else None,
        "supports_shopify": supplier.supports_shopify if supplier else None,
        "supports_automation": supplier.supports_automation if supplier else None,
        "provides_tracking": supplier.provides_tracking if supplier else None,
        "supports_returns": supplier.supports_returns if supplier else None,
        "return_policy_note": supplier.return_policy_note if supplier else None,
        "us_warehouse_capable": supplier.us_warehouse_capable if supplier else None,
        "us_warehouse_note": supplier.us_warehouse_note if supplier else None,
        "reliability_status": supplier.reliability_status if supplier else None,
        "reliability_note": supplier.reliability_note if supplier else None,
    }


def _serialize_scenario(scenario: FinancialScenario) -> dict[str, Any]:
    return {
        "id": scenario.id,
        "scenario_name": scenario.scenario_name,
        "selling_price": str(scenario.selling_price),
        "purchase_cost": str(scenario.purchase_cost),
        "shipping_cost": str(scenario.shipping_cost),
        "packaging_cost": str(scenario.packaging_cost),
        "other_landed_cost": str(scenario.other_landed_cost),
        "payment_processing_rate": str(scenario.payment_processing_rate),
        "payment_processing_fixed": str(scenario.payment_processing_fixed),
        "marketplace_fee_rate": str(scenario.marketplace_fee_rate),
        "marketplace_fee_fixed": str(scenario.marketplace_fee_fixed),
        "expected_return_rate": str(scenario.expected_return_rate),
        "customer_acquisition_cost": str(scenario.customer_acquisition_cost),
        "landed_fulfillment_cost": str(scenario.landed_fulfillment_cost),
        "variable_costs": str(scenario.variable_costs),
        "contribution_before_advertising": str(scenario.contribution_before_advertising),
        "contribution_after_advertising": str(scenario.contribution_after_advertising),
        "contribution_margin_after_advertising": str(scenario.contribution_margin_after_advertising),
        "break_even_cac": str(scenario.break_even_cac),
        "break_even_roas": str(scenario.break_even_roas) if scenario.break_even_roas else None,
        "notes": scenario.notes,
    }


def _serialize_observation(o: MarketObservation) -> dict[str, Any]:
    return {
        "id": o.id,
        "source_name": o.source_name,
        "source_url": o.source_url,
        "metric_name": o.metric_name,
        "value_text": o.value_text,
        "numeric_value": str(o.numeric_value) if o.numeric_value else None,
        "retrieval_timestamp": o.retrieval_timestamp.isoformat() if o.retrieval_timestamp else None,
        "data_classification": o.data_classification,
        "period": o.period,
        "notes": o.notes,
    }


def _serialize_source(source: ProductSource) -> dict[str, Any]:
    return {
        "id": source.id,
        "source_name": source.source_name,
        "source_type": source.source_type,
        "source_url": source.source_url,
        "retrieval_timestamp": source.retrieval_timestamp.isoformat() if source.retrieval_timestamp else None,
        "raw_value": source.raw_value,
        "data_classification": source.data_classification,
        "observation_period": source.observation_period,
        "notes": source.notes,
    }


def _serialize_social(o: SocialMediaObservation) -> dict[str, Any]:
    return {
        "id": o.id,
        "platform": o.platform,
        "content_url": o.content_url,
        "publication_date": o.publication_date,
        "view_count_text": o.view_count_text,
        "view_count_numeric": o.view_count_numeric,
        "like_count": o.like_count,
        "comment_count": o.comment_count,
        "share_count": o.share_count,
        "content_example_count": o.content_example_count,
        "advertising_activity_indicators": o.advertising_activity_indicators,
        "trend_direction": o.trend_direction,
        "retrieval_timestamp": o.retrieval_timestamp.isoformat() if o.retrieval_timestamp else None,
        "data_classification": o.data_classification,
        "notes": o.notes,
    }


def _serialize_competitor(c: Competitor) -> dict[str, Any]:
    return {
        "id": c.id,
        "source_name": c.source_name,
        "competitor_url": c.competitor_url,
        "asin": c.asin,
        "brand": c.brand,
        "title": c.title,
        "selling_price": str(c.selling_price),
        "review_count": c.review_count,
        "rating": str(c.rating) if c.rating else None,
        "sales_rank_text": c.sales_rank_text,
        "estimated_sales_text": c.estimated_sales_text,
        "differentiation": c.differentiation,
        "data_classification": c.data_classification,
        "retrieval_timestamp": c.retrieval_timestamp.isoformat() if c.retrieval_timestamp else None,
        "notes": c.notes,
    }


@router.post("/detail/{product_id}/sources", response_model=dict[str, Any])
async def add_product_source(
    product_id: int,
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    source = ProductSource(
        product_id=product.id,
        source_name=payload.get("source_name", "manual"),
        source_type=payload.get("source_type", "manual"),
        source_url=payload.get("source_url"),
        retrieval_timestamp=utc_now(),
        raw_value=payload.get("raw_value"),
        data_classification=payload.get("data_classification", "user_supplied"),
        observation_period=payload.get("observation_period"),
        notes=payload.get("notes"),
    )
    session.add(source)
    await session.commit()
    await session.refresh(source)
    return _serialize_source(source)


@router.post("/detail/{product_id}/suppliers", response_model=dict[str, Any])
async def add_product_supplier(
    product_id: int,
    payload: dict[str, Any],
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    supplier_name = payload.get("supplier_name")
    supplier_platform = payload.get("supplier_platform", "manual_entry")

    supplier = await session.execute(select(Supplier).where(Supplier.name == supplier_name, Supplier.platform == supplier_platform))
    supplier_row = supplier.scalar_one_or_none()
    if supplier_row is None:
        supplier_row = Supplier(
            name=supplier_name,
            platform=supplier_platform,
            website_url=payload.get("supplier_url"),
            supports_shopify=bool(payload.get("supports_shopify", False)),
            supports_automation=bool(payload.get("supports_automation", False)),
            provides_tracking=bool(payload.get("provides_tracking", False)),
            supports_returns=bool(payload.get("supports_returns", False)),
            return_policy_note=payload.get("return_policy_note"),
            us_warehouse_capable=bool(payload.get("us_warehouse_capable", False)),
            us_warehouse_note=payload.get("us_warehouse_note"),
            reliability_status="unassessed",
        )
        session.add(supplier_row)
        await session.flush()

    sp = SupplierProduct(
        supplier_id=supplier_row.id,
        product_id=product.id,
        supplier_product_url=payload.get("supplier_product_url"),
        supplier_product_name=payload.get("supplier_product_name") or product.name,
        purchase_cost=Decimal(str(payload.get("purchase_cost", "0"))),
        shipping_cost=Decimal(str(payload.get("shipping_cost", "0"))),
        processing_fee=Decimal(str(payload.get("processing_fee", "0"))),
        currency_code=payload.get("currency_code", "USD"),
        warehouse_origin=payload.get("warehouse_origin"),
        warehouse_verified=bool(payload.get("warehouse_verified", False)),
        warehouse_verification_status=payload.get("warehouse_verification_status", "unverified"),
        warehouse_verification_note=payload.get("warehouse_verification_note"),
        stock_available=bool(payload.get("stock_available", False)),
        stock_quantity=payload.get("stock_quantity"),
        processing_time_days=payload.get("processing_time_days"),
        delivery_estimate_days=payload.get("delivery_estimate_days"),
        shipping_service=payload.get("shipping_service"),
        destination_zip=payload.get("destination_zip"),
        evidence_status=payload.get("evidence_status", "user_supplied"),
        verification_timestamp=utc_now(),
    )
    session.add(sp)
    await session.commit()
    await session.refresh(sp)
    return _serialize_supplier(sp)


@router.get("/detail/{product_id}/financials/calculate", response_model=dict[str, Any])
async def calculate_product_financials(
    product_id: int,
    selling_price: str | None = Query(None),
    customer_acquisition_cost: str | None = Query(None),
    scenario_overrides: dict[str, Any] | None = None,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    price = Decimal(selling_price) if selling_price else product.suggested_retail_price or Decimal("0")
    cac = Decimal(customer_acquisition_cost) if customer_acquisition_cost else Decimal("0")
    scenario_overrides = scenario_overrides or {}

    components = CostComponents(
        purchase_cost=product.supplier_cost,
        shipping_cost=product.shipping_cost,
        packaging_cost=product.packaging_cost,
        other_landed_cost=product.other_landed_cost,
        payment_processing_rate=scenario_overrides.get("payment_rate", Decimal("0.029")),
        payment_processing_fixed=scenario_overrides.get("payment_fixed", Decimal("0.30")),
        marketplace_fee_rate=scenario_overrides.get("marketplace_rate", Decimal("0")),
        marketplace_fee_fixed=scenario_overrides.get("marketplace_fixed", Decimal("0")),
        expected_return_rate=scenario_overrides.get("return_rate", Decimal("0.05")),
        customer_acquisition_cost=cac,
        advertising_rate=scenario_overrides.get("advertising_rate"),
    )

    result_obj = calculate_financials(price, components)
    sensitivity_cacs = [Decimal("5"), Decimal("10"), Decimal("15"), Decimal("20"), Decimal("25")]
    sensitivity = build_sensitivity_table(price, components, sensitivity_cacs)

    return {
        "product_id": product.id,
        "selling_price": str(price),
        "result": result_obj.to_dict(),
        "sensitivity": [_serialize_sensitivity_row(r) for r in sensitivity],
        "assumptions": {
            "payment_rate": str(components.payment_processing_rate),
            "payment_fixed": str(components.payment_processing_fixed),
            "marketplace_rate": str(components.marketplace_fee_rate),
            "marketplace_fixed": str(components.marketplace_fee_fixed),
            "return_rate": str(components.expected_return_rate),
        },
    }


def _serialize_sensitivity_row(row: Any) -> dict[str, Any]:
    return {
        "cac": str(row.cac),
        "advertising_cost": str(row.advertising_cost),
        "contribution_after_advertising": str(row.contribution_after_advertising),
        "contribution_margin_after_advertising": str(row.contribution_margin_after_advertising),
    }


@router.get("/detail/{product_id}/ai/classify", response_model=dict[str, Any])
async def classify_product_ai(
    product_id: int,
    marketplace: str = Query("shopify"),
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    from app.ai.research_assistant import ProductSnapshotForAI, ClassificationRequest, classify_product
    from app.ai.providers import AIORchestrator
    from app.settings import get_settings

    orchestrator = AIORchestrator(get_settings())
    snapshot = ProductSnapshotForAI(
        name=product.name,
        description=product.description or "",
        category=product.category or "",
        brand=product.brand or "",
        asin=product.asin or "",
        product_url=product.product_url or "",
        supplier_cost=str(product.supplier_cost),
        shipping_cost=str(product.shipping_cost),
        suggested_retail_price=str(product.suggested_retail_price),
        us_warehouse_verified=product.us_warehouse_verified,
        us_warehouse_verification_status=product.us_warehouse_verification_status,
        estimated_delivery_days=str(product.estimated_delivery_days or ""),
        trend_classification=product.trend_classification,
        viral_potential=product.viral_potential,
        primary_competition_level=product.primary_competition_level,
        amazon_fulfillment_suitable=product.amazon_fulfillment_suitable,
        sources=[_serialize_source_simple(s) for s in (product.sources or [])],
        competitors=[_serialize_competitor_simple(c) for c in (product.competitors or [])],
        ai_provider_configured=orchestrator.is_configured,
        ai_status=orchestrator.status().get("status_message", ""),
    )
    response = await classify_product(orchestrator, ClassificationRequest(snapshot=snapshot, marketplace=marketplace))
    return response.model_dump()


def _serialize_source_simple(source: ProductSource) -> dict[str, str]:
    return {
        "source_name": source.source_name,
        "source_type": source.source_type,
        "source_url": source.source_url or "",
        "raw_value": source.raw_value or "",
        "data_classification": source.data_classification,
    }


def _serialize_competitor_simple(c: Competitor) -> dict[str, str]:
    return {
        "asin": c.asin or "",
        "brand": c.brand or "",
        "title": c.title or "",
        "selling_price": str(c.selling_price),
        "review_count": str(c.review_count) if c.review_count is not None else "",
        "rating": str(c.rating) if c.rating else "",
        "data_classification": c.data_classification,
    }


@router.get("/detail/{product_id}/ai/marketing", response_model=dict[str, Any])
async def marketing_plan_ai(
    product_id: int,
    marketplace: str = Query("shopify"),
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    from app.ai.research_assistant import ProductSnapshotForAI, MarketingPlanRequest, generate_marketing_plan
    from app.ai.providers import AIORchestrator
    from app.settings import get_settings

    orchestrator = AIORchestrator(get_settings())
    snapshot = ProductSnapshotForAI(
        name=product.name,
        description=product.description or "",
        category=product.category or "",
        brand=product.brand or "",
        asin=product.asin or "",
        product_url=product.product_url or "",
        supplier_cost=str(product.supplier_cost),
        shipping_cost=str(product.shipping_cost),
        suggested_retail_price=str(product.suggested_retail_price),
        us_warehouse_verified=product.us_warehouse_verified,
        us_warehouse_verification_status=product.us_warehouse_verification_status,
        estimated_delivery_days=str(product.estimated_delivery_days or ""),
        trend_classification=product.trend_classification,
        viral_potential=product.viral_potential,
        primary_competition_level=product.primary_competition_level,
        amazon_fulfillment_suitable=product.amazon_fulfillment_suitable,
        ai_provider_configured=orchestrator.is_configured,
        ai_status=orchestrator.status().get("status_message", ""),
    )
    response = await generate_marketing_plan(orchestrator, MarketingPlanRequest(snapshot=snapshot, marketplace=marketplace))
    return response.model_dump()


@router.get("/detail/{product_id}/ai/amazon-suitability", response_model=dict[str, Any])
async def amazon_suitability_ai(
    product_id: int,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    from app.ai.research_assistant import ProductSnapshotForAI, AmazonSuitabilityRequest, assess_amazon_suitability
    from app.ai.providers import AIORchestrator
    from app.settings import get_settings

    orchestrator = AIORchestrator(get_settings())
    snapshot = ProductSnapshotForAI(
        name=product.name,
        description=product.description or "",
        category=product.category or "",
        asin=product.asin or "",
        product_url=product.product_url or "",
        supplier_cost=str(product.supplier_cost),
        shipping_cost=str(product.shipping_cost),
        suggested_retail_price=str(product.suggested_retail_price),
        us_warehouse_verified=product.us_warehouse_verified,
        trend_classification=product.trend_classification,
        amazon_fulfillment_suitable=product.amazon_fulfillment_suitable,
        ai_provider_configured=orchestrator.is_configured,
        ai_status=orchestrator.status().get("status_message", ""),
    )
    response = await assess_amazon_suitability(orchestrator, AmazonSuitabilityRequest(snapshot=snapshot))
    return response.model_dump()


@router.get("/detail/{product_id}/ai/recommend", response_model=dict[str, Any])
async def recommend_product_ai(
    product_id: int,
    compare_with: list[int] | None = Query(None),
    marketplace: str = Query("shopify"),
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    ids = [product_id] + (compare_with or [])
    products: list[dict[str, Any]] = []
    for pid in ids:
        result = await session.execute(select(Product).where(Product.id == pid))
        product = result.scalar_one_or_none()
        if product is None:
            raise HTTPException(status_code=404, detail=f"Product {pid} not found")
        products.append(product)

    from app.ai.research_assistant import ProductSnapshotForAI, RecommendationRequest, recommend_product
    from app.ai.providers import AIORchestrator
    from app.settings import get_settings

    orchestrator = AIORchestrator(get_settings())
    snapshots = [
        ProductSnapshotForAI(
            name=p.name,
            description=p.description or "",
            category=p.category or "",
            asin=p.asin or "",
            product_url=p.product_url or "",
            supplier_cost=str(p.supplier_cost),
            shipping_cost=str(p.shipping_cost),
            suggested_retail_price=str(p.suggested_retail_price),
            us_warehouse_verified=p.us_warehouse_verified,
            trend_classification=p.trend_classification,
            viral_potential=p.viral_potential,
            primary_competition_level=p.primary_competition_level,
            amazon_fulfillment_suitable=p.amazon_fulfillment_suitable,
            ai_provider_configured=orchestrator.is_configured,
            ai_status=orchestrator.status().get("status_message", ""),
        )
        for p in products
    ]
    response = await recommend_product(orchestrator, RecommendationRequest(products=snapshots, marketplace=marketplace))
    return {
        "marketplace": marketplace,
        "products": [{"id": p.id, "name": p.name} for p in products],
        **response.model_dump(),
    }
