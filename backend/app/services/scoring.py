from __future__ import annotations

import datetime
from decimal import Decimal, ROUND_HALF_UP

from pydantic import BaseModel

from app.services.financial import calculate_financials, CostComponents


class ScoreComponent(BaseModel):
    name: str
    raw_value: Decimal
    score: int
    weight: Decimal
    notes: str = ""


class ScoringResult(BaseModel):
    total_score: int
    confidence_score: int
    marketplace: str
    model_version: str
    weights: dict[str, str]
    components: list[ScoreComponent]
    missing_fields: list[str]
    normalization_method: str
    calculated_at: str


DEFAULTS_USA_SHOPIFY = {
    "demand_evidence": Decimal("0.20"),
    "profitability": Decimal("0.20"),
    "verified_us_fulfillment": Decimal("0.20"),
    "marketing_potential": Decimal("0.15"),
    "competition_differentiation": Decimal("0.15"),
    "operational_risk": Decimal("0.10"),
}

DEFAULTS_USA_AMAZON = {
    "evidence_of_demand": Decimal("0.20"),
    "profitability": Decimal("0.20"),
    "competition_differentiation": Decimal("0.20"),
    "sourcing_fulfillment": Decimal("0.15"),
    "price_stability": Decimal("0.10"),
    "regulatory_operational_risk": Decimal("0.15"),
}


def normalize_score(raw: Decimal, scale_min: Decimal = Decimal("0"), scale_max: Decimal = Decimal("100")) -> int:
    if raw <= scale_min:
        return 0
    if raw >= scale_max:
        return 100
    normalized = ((raw - scale_min) / (scale_max - scale_min)) * Decimal("100")
    return int(normalized.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _weighted(component_score: int, weight: Decimal) -> Decimal:
    return Decimal(component_score) * weight


def score_shopify_product(
    product_name: str = "",
    supplier_verified: bool = False,
    contribution_margin_after_advertising: Decimal = Decimal("0"),
    break_even_cac: Decimal = Decimal("0"),
    demand_evidence_level: str = "insufficient_evidence",
    marketing_potential: str = "low",
    competition_level: str = "unknown",
    operational_risk: str = "unknown",
    weights: dict[str, Decimal] | None = None,
) -> ScoringResult:
    weights = weights or DEFAULTS_USA_SHOPIFY

    demand_map = {
        "emerging": Decimal("35"),
        "growing": Decimal("60"),
        "stable": Decimal("75"),
        "seasonal": Decimal("55"),
        "declining": Decimal("25"),
        "insufficient_evidence": Decimal("20"),
    }
    demand_score = normalize_score(demand_map.get(demand_evidence_level, Decimal("20")))

    profitability_score = normalize_score(
        contribution_margin_after_advertising
        if contribution_margin_after_advertising >= Decimal("0")
        else Decimal("-50"),
        scale_min=Decimal("-50"),
        scale_max=Decimal("60"),
    )

    us_fulfillment_score = Decimal("100") if supplier_verified else Decimal("25")

    marketing_map = {
        "very_high": Decimal("90"),
        "high": Decimal("75"),
        "medium": Decimal("55"),
        "low": Decimal("30"),
    }
    marketing_score = normalize_score(marketing_map.get(marketing_potential, Decimal("30")))

    competition_map = {
        "low": Decimal("85"),
        "moderate": Decimal("65"),
        "high": Decimal("35"),
        "unknown": Decimal("40"),
    }
    competition_score = normalize_score(competition_map.get(competition_level, Decimal("40")))

    risk_map = {
        "low": Decimal("85"),
        "moderate": Decimal("65"),
        "high": Decimal("35"),
        "unknown": Decimal("50"),
    }
    operational_score = normalize_score(risk_map.get(operational_risk, Decimal("50")))

    total = int(
        _weighted(demand_score, weights["demand_evidence"])
        + _weighted(profitability_score, weights["profitability"])
        + _weighted(int(us_fulfillment_score), weights["verified_us_fulfillment"])
        + _weighted(marketing_score, weights["marketing_potential"])
        + _weighted(competition_score, weights["competition_differentiation"])
        + _weighted(operational_score, weights["operational_risk"])
    )

    missing: list[str] = []
    if demand_evidence_level == "insufficient_evidence":
        missing.append("demand_evidence")
    if not supplier_verified:
        missing.append("verified_us_fulfillment")
    if marketing_potential == "low":
        missing.append("marketing_potential_estimate")

    confidence_score = int(
        Decimal("100")
        - (Decimal("15") if demand_evidence_level == "insufficient_evidence" else Decimal("0"))
        - (Decimal("20") if not supplier_verified else Decimal("0"))
        - (Decimal("10") if competition_level == "unknown" else Decimal("0"))
    )

    return ScoringResult(
        total_score=max(0, min(100, total)),
        confidence_score=max(0, min(100, confidence_score)),
        marketplace="shopify",
        model_version="1.0.0",
        weights={k: str(v) for k, v in weights.items()},
        components=[
            ScoreComponent(name="demand_evidence", raw_value=demand_map.get(demand_evidence_level, Decimal("0")), score=demand_score, weight=weights["demand_evidence"], notes=f"Demand level: {demand_evidence_level}"),
            ScoreComponent(name="profitability", raw_value=contribution_margin_after_advertising, score=profitability_score, weight=weights["profitability"], notes="Contribution margin after advertising"),
            ScoreComponent(name="verified_us_fulfillment", raw_value=us_fulfillment_score, score=int(us_fulfillment_score), weight=weights["verified_us_fulfillment"], notes="Supplier US warehouse verification status"),
            ScoreComponent(name="marketing_potential", raw_value=marketing_map.get(marketing_potential, Decimal("0")), score=marketing_score, weight=weights["marketing_potential"], notes=f"Marketing potential: {marketing_potential}"),
            ScoreComponent(name="competition_differentiation", raw_value=competition_map.get(competition_level, Decimal("0")), score=competition_score, weight=weights["competition_differentiation"], notes=f"Competition: {competition_level}"),
            ScoreComponent(name="operational_risk", raw_value=risk_map.get(operational_risk, Decimal("0")), score=operational_score, weight=weights["operational_risk"], notes=f"Operational risk: {operational_risk}"),
        ],
        missing_fields=missing,
        normalization_method="min_max",
        calculated_at="",  # Set by caller
    )


def score_amazon_product(
    demand_level: str = "insufficient_evidence",
    contribution_margin_after_advertising: Decimal = Decimal("0"),
    competition_level: str = "unknown",
    sourcing_risk: str = "unknown",
    price_stability: str = "unknown",
    regulatory_risk: str = "unknown",
    weights: dict[str, Decimal] | None = None,
) -> ScoringResult:
    weights = weights or DEFAULTS_USA_AMAZON

    demand_map = {
        "emerging": Decimal("35"),
        "growing": Decimal("60"),
        "stable": Decimal("75"),
        "seasonal": Decimal("55"),
        "declining": Decimal("25"),
        "insufficient_evidence": Decimal("20"),
    }
    demand_score = normalize_score(demand_map.get(demand_level, Decimal("20")))

    profitability_score = normalize_score(
        contribution_margin_after_advertising
        if contribution_margin_after_advertising >= Decimal("0")
        else Decimal("-50"),
        scale_min=Decimal("-50"),
        scale_max=Decimal("60"),
    )

    competition_map = {
        "low": Decimal("85"),
        "moderate": Decimal("65"),
        "high": Decimal("35"),
        "unknown": Decimal("40"),
    }
    competition_score = normalize_score(competition_map.get(competition_level, Decimal("40")))

    sourcing_map = {
        "strong": Decimal("85"),
        "moderate": Decimal("60"),
        "weak": Decimal("30"),
        "unassessed": Decimal("45"),
        "unknown": Decimal("40"),
    }
    sourcing_score = normalize_score(sourcing_map.get(sourcing_risk, Decimal("40")))

    price_map = {
        "stable": Decimal("80"),
        "moderate": Decimal("60"),
        "volatile": Decimal("35"),
        "unknown": Decimal("50"),
    }
    price_score = normalize_score(price_map.get(price_stability, Decimal("50")))

    risk_map = {
        "low": Decimal("85"),
        "moderate": Decimal("60"),
        "high": Decimal("30"),
        "unassessed": Decimal("50"),
        "unknown": Decimal("45"),
    }
    risk_score = normalize_score(risk_map.get(regulatory_risk, Decimal("45")))

    total = int(
        _weighted(demand_score, weights["evidence_of_demand"])
        + _weighted(profitability_score, weights["profitability"])
        + _weighted(competition_score, weights["competition_differentiation"])
        + _weighted(sourcing_score, weights["sourcing_fulfillment"])
        + _weighted(price_score, weights["price_stability"])
        + _weighted(risk_score, weights["regulatory_operational_risk"])
    )

    missing: list[str] = []
    if demand_level == "insufficient_evidence":
        missing.append("evidence_of_demand")
    if sourcing_risk in {"unassessed", "unknown"}:
        missing.append("sourcing_fulfillment")
    if regulatory_risk in {"unassessed", "unknown"}:
        missing.append("regulatory_operational_risk")

    confidence_score = int(
        Decimal("100")
        - (Decimal("15") if demand_level == "insufficient_evidence" else Decimal("0"))
        - (Decimal("15") if sourcing_risk in {"unassessed", "unknown"} else Decimal("0"))
        - (Decimal("10") if regulatory_risk in {"unassessed", "unknown"} else Decimal("0"))
    )

    return ScoringResult(
        total_score=max(0, min(100, total)),
        confidence_score=max(0, min(100, confidence_score)),
        marketplace="amazon",
        model_version="1.0.0",
        weights={k: str(v) for k, v in weights.items()},
        components=[
            ScoreComponent(name="evidence_of_demand", raw_value=demand_map.get(demand_level, Decimal("0")), score=demand_score, weight=weights["evidence_of_demand"], notes=f"Demand level: {demand_level}"),
            ScoreComponent(name="profitability", raw_value=contribution_margin_after_advertising, score=profitability_score, weight=weights["profitability"], notes="Contribution margin after advertising"),
            ScoreComponent(name="competition_differentiation", raw_value=competition_map.get(competition_level, Decimal("0")), score=competition_score, weight=weights["competition_differentiation"], notes=f"Competition: {competition_level}"),
            ScoreComponent(name="sourcing_fulfillment", raw_value=sourcing_map.get(sourcing_risk, Decimal("0")), score=sourcing_score, weight=weights["sourcing_fulfillment"], notes=f"Sourcing risk: {sourcing_risk}"),
            ScoreComponent(name="price_stability", raw_value=price_map.get(price_stability, Decimal("0")), score=price_score, weight=weights["price_stability"], notes=f"Price stability: {price_stability}"),
            ScoreComponent(name="regulatory_operational_risk", raw_value=risk_map.get(regulatory_risk, Decimal("0")), score=risk_score, weight=weights["regulatory_operational_risk"], notes=f"Regulatory/operational risk: {regulatory_risk}"),
        ],
        missing_fields=missing,
        normalization_method="min_max",
        calculated_at="",  # Set by caller
    )
