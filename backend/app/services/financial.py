from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from pydantic import BaseModel


def round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class CostComponents(BaseModel):
    purchase_cost: Decimal = Decimal("0.0000")
    shipping_cost: Decimal = Decimal("0.0000")
    packaging_cost: Decimal = Decimal("0.0000")
    other_landed_cost: Decimal = Decimal("0.0000")
    payment_processing_rate: Decimal = Decimal("0.0000")
    payment_processing_fixed: Decimal = Decimal("0.0000")
    marketplace_fee_rate: Decimal = Decimal("0.0000")
    marketplace_fee_fixed: Decimal = Decimal("0.0000")
    expected_return_rate: Decimal = Decimal("0.0000")
    customer_acquisition_cost: Decimal = Decimal("0.0000")
    advertising_rate: Decimal | None = None


class FinancialResult(BaseModel):
    selling_price: Decimal
    gross_revenue: Decimal
    landed_fulfillment_cost: Decimal
    payment_fees: Decimal
    marketplace_fees: Decimal
    expected_return_cost: Decimal
    variable_costs: Decimal
    contribution_before_advertising: Decimal
    advertising_cost: Decimal
    contribution_after_advertising: Decimal
    contribution_margin_after_advertising: Decimal
    break_even_cac: Decimal
    break_even_roas: Decimal | None
    net_per_unit_before_fixed: Decimal
    fixed_cost_per_unit_placeholder: Decimal = Decimal("0.0000")

    def to_dict(self) -> dict[str, Any]:
        return {
            "selling_price": str(self.selling_price),
            "gross_revenue": str(self.gross_revenue),
            "landed_fulfillment_cost": str(self.landed_fulfillment_cost),
            "payment_fees": str(self.payment_fees),
            "marketplace_fees": str(self.marketplace_fees),
            "expected_return_cost": str(self.expected_return_cost),
            "variable_costs": str(self.variable_costs),
            "contribution_before_advertising": str(self.contribution_before_advertising),
            "advertising_cost": str(self.advertising_cost),
            "contribution_after_advertising": str(self.contribution_after_advertising),
            "contribution_margin_after_advertising": str(
                self.contribution_margin_after_advertising
            ),
            "break_even_cac": str(self.break_even_cac),
            "break_even_roas": str(self.break_even_roas)
            if self.break_even_roas is not None
            else None,
            "net_per_unit_before_fixed": str(self.net_per_unit_before_fixed),
        }


def calculate_financials(
    selling_price: Decimal,
    components: CostComponents,
) -> FinancialResult:
    selling_price = selling_price.max(Decimal("0.0000"))

    landed_fulfillment_cost = (
        components.purchase_cost
        + components.shipping_cost
        + components.packaging_cost
        + components.other_landed_cost
    )

    payment_fees = (
        selling_price * components.payment_processing_rate
        + components.payment_processing_fixed
    )

    marketplace_fees = (
        selling_price * components.marketplace_fee_rate
        + components.marketplace_fee_fixed
    )

    expected_return_cost = selling_price * components.expected_return_rate

    variable_costs = (
        landed_fulfillment_cost
        + payment_fees
        + marketplace_fees
        + expected_return_cost
    )

    contribution_before_advertising = selling_price - variable_costs
    advertising_cost = components.customer_acquisition_cost
    contribution_after_advertising = contribution_before_advertising - advertising_cost

    if selling_price > Decimal("0.0000"):
        contribution_margin_after_advertising = (
            contribution_after_advertising / selling_price
        ) * Decimal("100")
    else:
        contribution_margin_after_advertising = Decimal("0")

    break_even_cac = contribution_before_advertising
    if selling_price > Decimal("0.0000") and advertising_cost > Decimal("0"):
        break_even_roas = selling_price / advertising_cost
    else:
        break_even_roas = None

    net_per_unit_before_fixed = contribution_after_advertising

    return FinancialResult(
        selling_price=selling_price,
        gross_revenue=selling_price,
        landed_fulfillment_cost=round_money(landed_fulfillment_cost),
        payment_fees=round_money(payment_fees),
        marketplace_fees=round_money(marketplace_fees),
        expected_return_cost=round_money(expected_return_cost),
        variable_costs=round_money(variable_costs),
        contribution_before_advertising=round_money(contribution_before_advertising),
        advertising_cost=round_money(advertising_cost),
        contribution_after_advertising=round_money(contribution_after_advertising),
        contribution_margin_after_advertising=round_money(
            contribution_margin_after_advertising
        ),
        break_even_cac=round_money(break_even_cac),
        break_even_roas=round_money(break_even_roas) if break_even_roas is not None else None,
        net_per_unit_before_fixed=round_money(net_per_unit_before_fixed),
    )


class SensitivityRow(BaseModel):
    cac: Decimal
    advertising_cost: Decimal
    contribution_after_advertising: Decimal
    contribution_margin_after_advertising: Decimal


def build_sensitivity_table(
    selling_price: Decimal,
    components: CostComponents,
    cac_values: list[Decimal],
) -> list[SensitivityRow]:
    rows: list[SensitivityRow] = []
    for cac in cac_values:
        result = calculate_financials(
            selling_price,
            CostComponents(
                purchase_cost=components.purchase_cost,
                shipping_cost=components.shipping_cost,
                packaging_cost=components.packaging_cost,
                other_landed_cost=components.other_landed_cost,
                payment_processing_rate=components.payment_processing_rate,
                payment_processing_fixed=components.payment_processing_fixed,
                marketplace_fee_rate=components.marketplace_fee_rate,
                marketplace_fee_fixed=components.marketplace_fee_fixed,
                expected_return_rate=components.expected_return_rate,
                customer_acquisition_cost=cac,
                advertising_rate=components.advertising_rate,
            ),
        )
        rows.append(
            SensitivityRow(
                cac=round_money(cac),
                advertising_cost=round_money(result.advertising_cost),
                contribution_after_advertising=round_money(
                    result.contribution_after_advertising
                ),
                contribution_margin_after_advertising=result.contribution_margin_after_advertising,
            )
        )
    return rows


def build_scenario_results(
    selling_price: Decimal,
    purchase_cost: Decimal,
    shipping_cost: Decimal,
    packaging_cost: Decimal = Decimal("0"),
    other_landed_cost: Decimal = Decimal("0"),
    payment_rate: Decimal = Decimal("0.029"),
    payment_fixed: Decimal = Decimal("0.30"),
    marketplace_rate: Decimal = Decimal("0"),
    marketplace_fixed: Decimal = Decimal("0"),
    return_rate: Decimal = Decimal("0.05"),
    base_cac: Decimal = Decimal("15"),
    scenario_overrides: dict[str, dict[str, Decimal]] | None = None,
) -> dict[str, FinancialResult]:
    scenario_overrides = scenario_overrides or {}

    def make_scenario(name: str, multiplier: Decimal) -> FinancialResult:
        overrides = scenario_overrides.get(name, {})
        adj = CostComponents(
            purchase_cost=overrides.get("purchase_cost", purchase_cost * multiplier),
            shipping_cost=overrides.get("shipping_cost", shipping_cost * multiplier),
            packaging_cost=overrides.get("packaging_cost", packaging_cost * multiplier),
            other_landed_cost=overrides.get("other_landed_cost", other_landed_cost * multiplier),
            payment_processing_rate=overrides.get("payment_rate", payment_rate),
            payment_processing_fixed=overrides.get("payment_fixed", payment_fixed),
            marketplace_fee_rate=overrides.get("marketplace_rate", marketplace_rate),
            marketplace_fee_fixed=overrides.get("marketplace_fixed", marketplace_fixed),
            expected_return_rate=overrides.get("return_rate", return_rate * multiplier),
            customer_acquisition_cost=overrides.get("cac", base_cac * multiplier),
            advertising_rate=None,
        )
        return calculate_financials(selling_price, adj)

    return {
        "optimistic": make_scenario("optimistic", Decimal("0.9")),
        "base": make_scenario("base", Decimal("1")),
        "pessimistic": make_scenario("pessimistic", Decimal("1.15")),
    }
