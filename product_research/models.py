from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

VerificationStatus = Literal["verified", "estimated", "missing", "unverified", "requires_quote"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SourceValue:
    value: Any
    source: str
    collected_at: str
    verification_status: VerificationStatus
    confidence: str = "medium"


@dataclass
class ProductCandidate:
    asin: str
    name: str
    category: str
    marketplace: str
    product_url: str
    price: SourceValue
    reviews: SourceValue | None = None
    rating: SourceValue | None = None
    bsr: SourceValue | None = None
    sales_estimate: SourceValue | None = None
    sellers: SourceValue | None = None
    fulfillment: SourceValue | None = None


@dataclass
class SupplierLead:
    supplier_name: str
    platform: str
    product_link: str
    unit_purchase_price: float | None
    minimum_order_quantity: int | None
    verification_status: VerificationStatus
    notes: str = ""


@dataclass
class ProfitScenario:
    name: str
    landed_cost: float | None
    profit_per_unit: float | None
    profit_margin: float | None
    roi: float | None
    break_even_price: float | None
    break_even_ad_cost: float | None
    incomplete_reason: str | None = None


@dataclass
class AiAnalysis:
    opportunity_score: float
    data_confidence: str
    demand_assessment: str
    competition_assessment: str
    profitability_assessment: str
    differentiation_recommendations: list[str]
    main_risks: list[str]
    recommended_next_actions: list[str]
    verification_notes: list[str]
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchResult:
    product: ProductCandidate
    suppliers: list[SupplierLead]
    profit_scenarios: list[ProfitScenario]
    ai_analysis: AiAnalysis
    status: str

