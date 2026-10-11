from __future__ import annotations

from dataclasses import asdict

from product_research.models import ProductCandidate, ProfitScenario, SupplierLead


def product_fingerprint(product: ProductCandidate) -> str:
    return f"{product.marketplace}:{product.asin}".lower()


def summarize_data_quality(
    product: ProductCandidate,
    suppliers: list[SupplierLead],
    profit_scenarios: list[ProfitScenario],
) -> dict[str, object]:
    verified = []
    estimated = []
    missing = []

    fields = {
        "price": product.price,
        "reviews": product.reviews,
        "rating": product.rating,
        "bsr": product.bsr,
        "sales_estimate": product.sales_estimate,
        "sellers": product.sellers,
        "fulfillment": product.fulfillment,
    }
    for name, source_value in fields.items():
        if source_value is None or source_value.value is None:
            missing.append(name)
        elif source_value.verification_status == "verified":
            verified.append(name)
        elif source_value.verification_status == "estimated":
            estimated.append(name)
        else:
            missing.append(name)

    if not any(lead.verification_status == "verified" and lead.unit_purchase_price is not None for lead in suppliers):
        missing.append("verified_supplier_quote")

    if any(scenario.incomplete_reason for scenario in profit_scenarios):
        missing.append("complete_profitability")

    return {
        "fingerprint": product_fingerprint(product),
        "verified_data": sorted(set(verified)),
        "estimated_data": sorted(set(estimated)),
        "missing_data": sorted(set(missing)),
        "supplier_verification": [asdict(lead) for lead in suppliers],
    }

