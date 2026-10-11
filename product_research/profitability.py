from __future__ import annotations

from dataclasses import dataclass

from product_research.models import ProductCandidate, ProfitScenario, SupplierLead


@dataclass(frozen=True)
class CostAssumptions:
    referral_fee_rate: float = 0.15
    vat_rate: float = 0.05
    ad_cost_rate: float = 0.10
    return_allowance_rate: float = 0.03
    packaging_cost: float = 2.0
    shipping_cost: float = 8.0
    customs_rate: float = 0.05
    prices_include_vat: bool = True


class ProfitabilityCalculator:
    def __init__(self, assumptions: CostAssumptions | None = None) -> None:
        self.assumptions = assumptions or CostAssumptions()

    def calculate(self, product: ProductCandidate, suppliers: list[SupplierLead]) -> list[ProfitScenario]:
        supplier_costs = [lead.unit_purchase_price for lead in suppliers if lead.unit_purchase_price is not None]
        if not supplier_costs:
            return [
                ProfitScenario(name, None, None, None, None, None, None, "Missing verified supplier unit cost")
                for name in ["best", "expected", "worst"]
            ]
        base_cost = min(supplier_costs)
        factors = {"best": 0.90, "expected": 1.0, "worst": 1.15}
        return [self._scenario(product, base_cost * factor, name) for name, factor in factors.items()]

    def _scenario(self, product: ProductCandidate, purchase_cost: float, name: str) -> ProfitScenario:
        a = self.assumptions
        selling_price = float(product.price.value)
        net_revenue = selling_price / (1 + a.vat_rate) if a.prices_include_vat else selling_price
        customs = purchase_cost * a.customs_rate
        referral_fee = net_revenue * a.referral_fee_rate
        ad_cost = net_revenue * a.ad_cost_rate
        return_allowance = net_revenue * a.return_allowance_rate
        landed_cost = purchase_cost + a.shipping_cost + customs + a.packaging_cost
        total_cost = landed_cost + referral_fee + ad_cost + return_allowance
        profit = net_revenue - total_cost
        margin = profit / net_revenue if net_revenue else None
        roi = profit / landed_cost if landed_cost else None
        break_even_price = total_cost * (1 + a.vat_rate) if a.prices_include_vat else total_cost
        break_even_ad_cost = max(0.0, net_revenue - (landed_cost + referral_fee + return_allowance))
        return ProfitScenario(name, round(landed_cost, 2), round(profit, 2), _round_ratio(margin), _round_ratio(roi), round(break_even_price, 2), round(break_even_ad_cost, 2))


def _round_ratio(value: float | None) -> float | None:
    return None if value is None else round(value, 4)

