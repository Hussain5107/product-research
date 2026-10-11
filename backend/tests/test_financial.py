from __future__ import annotations

from decimal import Decimal

from app.services.financial import CostComponents, calculate_financials


def test_calculate_financials_is_deterministic() -> None:
    result = calculate_financials(
        Decimal("49.99"),
        CostComponents(
            purchase_cost=Decimal("12.50"),
            shipping_cost=Decimal("4.25"),
            packaging_cost=Decimal("0.75"),
            other_landed_cost=Decimal("1.50"),
            payment_processing_rate=Decimal("0.029"),
            payment_processing_fixed=Decimal("0.30"),
            marketplace_fee_rate=Decimal("0.15"),
            expected_return_rate=Decimal("0.05"),
            customer_acquisition_cost=Decimal("8.00"),
        ),
    )

    assert result.landed_fulfillment_cost == Decimal("19.00")
    assert result.payment_fees == Decimal("1.75")
    assert result.marketplace_fees == Decimal("7.50")
    assert result.expected_return_cost == Decimal("2.50")
    assert result.contribution_before_advertising == Decimal("19.24")
    assert result.contribution_after_advertising == Decimal("11.24")
    assert result.contribution_margin_after_advertising == Decimal("22.49")
    assert result.break_even_cac == Decimal("19.24")
