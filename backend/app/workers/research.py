from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product, Region
from app.models.research import ResearchRun, ResearchStatus, OpportunityScore, FinancialScenario, MarketObservation, SocialMediaObservation, Competitor
from app.models.supplier import Supplier, SupplierProduct
from app.services.financial import CostComponents, calculate_financials
from app.services.scoring import score_shopify_product, score_amazon_product
from app.connectors.registry import ConnectorRegistry


async def update_run_stage(
    session: AsyncSession,
    run_id: int,
    stage: str,
    message: str | None = None,
) -> None:
    result = await session.execute(select(ResearchRun).where(ResearchRun.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        return
    run.current_stage = stage
    run.progress_message = message or ""
    await session.commit()


async def increment_run_counter(
    session: AsyncSession,
    run_id: int,
    counter_name: str,
    increment: int = 1,
) -> None:
    result = await session.execute(select(ResearchRun).where(ResearchRun.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        return
    current = getattr(run, counter_name, 0)
    setattr(run, counter_name, current + increment)
    await session.commit()


async def complete_run(
    session: AsyncSession,
    run_id: int,
    status: str,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> None:
    result = await session.execute(select(ResearchRun).where(ResearchRun.id == run_id))
    run = result.scalar_one_or_none()
    if run is None:
        return
    run.status = ResearchStatus(status)
    run.research_end = datetime.datetime.utcnow()
    if warnings is not None:
        run.warnings = warnings
    if errors is not None:
        run.errors = errors
    await session.commit()


class ResearchWorkflow:
    def __init__(self, session: AsyncSession, run_id: int, registry: ConnectorRegistry | None = None):
        self.session = session
        self.run_id = run_id
        self.registry = registry or ConnectorRegistry()
        self.connectors = self.registry.all()
        self.suppliers: list[Supplier] = []
        self.errors: list[str] = []
        self.warnings: list[str] = []

    async def run(self) -> dict[str, Any]:
        try:
            await update_run_stage(self.session, self.run_id, "discovering_candidates", "Discovering product candidates...")
            candidates = await self._discover_candidates()
            await increment_run_counter(self.session, self.run_id, "candidates_discovered", len(candidates))

            await update_run_stage(self.session, self.run_id, "validating_demand", "Checking market demand...")
            products = await self._build_products(candidates)
            await increment_run_counter(self.session, self.run_id, "products_analyzed", len(products))

            await update_run_stage(self.session, self.run_id, "analyzing_competition", "Analyzing competition...")
            await self._analyze_competition(products)

            await update_run_stage(self.session, self.run_id, "searching_suppliers", "Searching suppliers...")
            await self._find_suppliers(products)
            await increment_run_counter(self.session, self.run_id, "suppliers_checked", len(self.suppliers))

            await update_run_stage(self.session, self.run_id, "verifying_us_warehouses", "Verifying US warehouses...")
            await self._verify_warehouses(products)

            await update_run_stage(self.session, self.run_id, "calculating_profitability", "Calculating profitability...")
            await self._calculate_economics(products)

            await update_run_stage(self.session, self.run_id, "generating_recommendations", "Generating recommendations...")
            await self._score_and_recommend(products)

            await complete_run(self.session, self.run_id, "completed", warnings=self.warnings)
            return {
                "status": "completed",
                "products_count": len(products),
                "suppliers_count": len(self.suppliers),
                "warnings": self.warnings,
                "errors": self.errors,
            }
        except Exception as e:
            self.errors.append(str(e))
            await complete_run(self.session, self.run_id, "failed", errors=self.errors)
            raise

    async def _discover_candidates(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for connector in self.connectors:
            try:
                obs = await connector.fetch_trend_observations("home organization", period="30d")
                results.extend(obs)
            except Exception as e:
                self.warnings.append(f"{connector.name} trend fetch failed: {e}")
        return results

    async def _build_products(self, candidates: list[dict[str, Any]]) -> list[Product]:
        region_result = await self.session.execute(select(Region).where(Region.code == "US"))
        region = region_result.scalar_one_or_none()
        if region is None:
            raise RuntimeError("US region not found. Initialization may be incomplete.")

        products: list[Product] = []
        seen: set[str] = set()
        for idx, candidate in enumerate(candidates[:20]):
            name = candidate.get("keyword") or f"Research Candidate {idx + 1}"
            if name in seen:
                continue
            seen.add(name)
            product = Product(
                region_id=region.id,
                name=name,
                description=candidate.get("note") or "Research candidate created during discovery workflow.",
                category=candidate.get("source") or "unknown",
                supplier_cost=Decimal("0.0000"),
                shipping_cost=Decimal("0.0000"),
                packaging_cost=Decimal("0.0000"),
                other_landed_cost=Decimal("0.0000"),
                suggested_retail_price=Decimal("0.0000"),
                us_warehouse_verified=False,
                us_warehouse_verification_status="unverified",
                amazon_fulfillment_suitable="needs_review",
                trend_classification="insufficient_evidence",
                viral_potential="low",
                primary_competition_level="unknown",
                status="candidate",
            )
            self.session.add(product)
            products.append(product)
        await self.session.flush()
        return list({p.id: p for p in products}.values())

    async def _analyze_competition(self, products: list[Product]) -> None:
        for product in products:
            competitor = Competitor(
                product_id=product.id,
                source_name="manual_addition",
                title=product.name,
                selling_price=product.suggested_retail_price,
                data_classification="unverified",
                notes="Placeholder competitor record created during Phase 1 workflow.",
                retrieval_timestamp=datetime.datetime.utcnow(),
            )
            self.session.add(competitor)
        await self.session.flush()

    async def _find_suppliers(self, products: list[Product]) -> None:
        for product in products:
            supplier = Supplier(
                name="Example Supplier",
                platform="manual_entry",
                website_url="",
                supports_shopify=False,
                supports_automation=False,
                provides_tracking=False,
                supports_returns=False,
                us_warehouse_capable=False,
                reliability_status="unassessed",
            )
            self.session.add(supplier)
            self.suppliers.append(supplier)
        await self.session.flush()
        self.suppliers = list({s.id: s for s in self.suppliers}.values())
        for supplier in self.suppliers:
            for product in products:
                sp = SupplierProduct(
                    supplier_id=supplier.id,
                    product_id=product.id,
                    supplier_product_name=product.name,
                    purchase_cost=Decimal("0.0000"),
                    shipping_cost=Decimal("0.0000"),
                    processing_fee=Decimal("0.0000"),
                    warehouse_verified=False,
                    warehouse_verification_status="unverified",
                    evidence_status="unverified",
                    verification_timestamp=datetime.datetime.utcnow(),
                )
                self.session.add(sp)
        await self.session.flush()

    async def _verify_warehouses(self, products: list[Product]) -> None:
        for product in products:
            product.us_warehouse_verification_status = "unverified"
            product.us_warehouse_verified = False
        await self.session.flush()

    async def _calculate_economics(self, products: list[Product]) -> None:
        for product in products:
            result = calculate_financials(
                product.suggested_retail_price or Decimal("0"),
                CostComponents(
                    purchase_cost=product.supplier_cost,
                    shipping_cost=product.shipping_cost,
                    packaging_cost=product.packaging_cost,
                    other_landed_cost=product.other_landed_cost,
                    payment_processing_rate=Decimal("0.029"),
                    payment_processing_fixed=Decimal("0.30"),
                    marketplace_fee_rate=Decimal("0"),
                    marketplace_fee_fixed=Decimal("0"),
                    expected_return_rate=Decimal("0.05"),
                    customer_acquisition_cost=Decimal("0"),
                    advertising_rate=None,
                ),
            )
            scenario = FinancialScenario(
                product_id=product.id,
                research_run_id=self.run_id,
                scenario_name="base",
                selling_price=product.suggested_retail_price or Decimal("0"),
                purchase_cost=product.supplier_cost,
                shipping_cost=product.shipping_cost,
                packaging_cost=product.packaging_cost,
                other_landed_cost=product.other_landed_cost,
                payment_processing_rate=Decimal("0.029"),
                payment_processing_fixed=Decimal("0.30"),
                marketplace_fee_rate=Decimal("0"),
                marketplace_fee_fixed=Decimal("0"),
                expected_return_rate=Decimal("0.05"),
                customer_acquisition_cost=Decimal("0"),
                landed_fulfillment_cost=result.landed_fulfillment_cost,
                variable_costs=result.variable_costs,
                contribution_before_advertising=result.contribution_before_advertising,
                contribution_after_advertising=result.contribution_after_advertising,
                contribution_margin_after_advertising=result.contribution_margin_after_advertising,
                break_even_cac=result.break_even_cac,
                break_even_roas=result.break_even_roas,
            )
            self.session.add(scenario)

    async def _score_and_recommend(self, products: list[Product]) -> None:
        for product in products:
            calculated_at = datetime.datetime.utcnow()
            shopify_score = score_shopify_product(
                product_name=product.name,
                supplier_verified=product.us_warehouse_verified,
                contribution_margin_after_advertising=Decimal("0"),
                break_even_cac=Decimal("0"),
                demand_evidence_level="insufficient_evidence",
                marketing_potential="low",
                competition_level="unknown",
                operational_risk="unknown",
            )
            amazon_score = score_amazon_product(
                demand_level="insufficient_evidence",
                contribution_margin_after_advertising=Decimal("0"),
                competition_level="unknown",
                sourcing_risk="unassessed",
                price_stability="unknown",
                regulatory_risk="unknown",
            )

            if product.id is not None:
                sp = OpportunityScore(
                    product_id=product.id,
                    research_run_id=self.run_id,
                    marketplace="shopify",
                    total_score=shopify_score.total_score,
                    confidence_score=shopify_score.confidence_score,
                    weights_json=shopify_score.weights,
                    component_scores_json={
                        c.name: {"score": c.score, "raw_value": str(c.raw_value), "notes": c.notes}
                        for c in shopify_score.components
                    },
                    missing_fields_json=shopify_score.missing_fields,
                    normalization_method=shopify_score.normalization_method,
                    scoring_model_version=shopify_score.model_version,
                    calculated_at=calculated_at,
                )
                self.session.add(sp)

                ap = OpportunityScore(
                    product_id=product.id,
                    research_run_id=self.run_id,
                    marketplace="amazon",
                    total_score=amazon_score.total_score,
                    confidence_score=amazon_score.confidence_score,
                    weights_json=amazon_score.weights,
                    component_scores_json={
                        c.name: {"score": c.score, "raw_value": str(c.raw_value), "notes": c.notes}
                        for c in amazon_score.components
                    },
                    missing_fields_json=amazon_score.missing_fields,
                    normalization_method=amazon_score.normalization_method,
                    scoring_model_version=amazon_score.model_version,
                    calculated_at=calculated_at,
                )
                self.session.add(ap)
        await self.session.flush()
