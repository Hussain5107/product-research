from __future__ import annotations

from decimal import Decimal

from app.services.global_deals import ExchangeRateInput, GlobalOfferInput, rank_global_offers


def test_rank_global_offers_uses_total_delivered_cost_in_aed() -> None:
    offers = [
        GlobalOfferInput(
            marketplace="Amazon UAE",
            product_name="Sony WF-1000XM5",
            product_url="https://www.amazon.ae/dp/example-ae",
            seller="Amazon",
            currency="AED",
            product_price=Decimal("899"),
            shipping_cost=Decimal("0"),
            import_charges=Decimal("0"),
            taxes=Decimal("0"),
            uae_delivery_eligible=True,
            comparable_status="exact_match",
            verification_status="shipping_quote_verified",
        ),
        GlobalOfferInput(
            marketplace="Amazon Germany",
            product_name="Sony WF-1000XM5",
            product_url="https://www.amazon.de/dp/example-de",
            seller="Amazon EU",
            currency="EUR",
            product_price=Decimal("160"),
            discount_amount=Decimal("20"),
            shipping_cost=Decimal("18"),
            import_charges=Decimal("12"),
            taxes=Decimal("0"),
            card_fx_markup_rate=Decimal("0.02"),
            uae_delivery_eligible=True,
            comparable_status="equivalent_regional_version",
            verification_status="shipping_quote_verified",
        ),
    ]
    rates = [
        ExchangeRateInput(from_currency="AED", to_currency="AED", rate=Decimal("1")),
        ExchangeRateInput(from_currency="EUR", to_currency="AED", rate=Decimal("4")),
    ]

    result = rank_global_offers(offers, rates)

    assert [offer.marketplace for offer in result.top_offers] == ["Amazon Germany", "Amazon UAE"]
    assert result.top_offers[0].total_delivered_cost == Decimal("173.40")
    assert result.top_offers[0].total_delivered_cost_aed == Decimal("693.60")
    assert result.top_offers[0].rank == 1


def test_rank_global_offers_excludes_incomplete_or_non_comparable_offers() -> None:
    offers = [
        GlobalOfferInput(
            marketplace="Amazon USA",
            product_name="Sony WF-1000XM5 used-like title",
            product_url="https://www.amazon.com/dp/example-us",
            currency="USD",
            product_price=Decimal("120"),
            shipping_cost=None,
            import_charges=Decimal("0"),
            taxes=Decimal("0"),
            uae_delivery_eligible=None,
            comparable_status="similar_product",
            verification_status="incomplete",
        )
    ]
    rates = [ExchangeRateInput(from_currency="USD", to_currency="AED", rate=Decimal("3.67"))]

    result = rank_global_offers(offers, rates)

    assert result.top_offers == []
    assert len(result.similar_or_incomplete_offers) == 1
    excluded = result.similar_or_incomplete_offers[0]
    assert excluded.total_delivered_cost_aed is None
    assert "Product is not classified as an exact or equivalent regional match." in excluded.exclusion_reasons
    assert "UAE delivery eligibility is not verified." in excluded.exclusion_reasons
    assert "Shipping cost is unavailable." in excluded.exclusion_reasons


def test_offer_rejects_discount_larger_than_price() -> None:
    try:
        GlobalOfferInput(
            marketplace="Amazon UK",
            product_name="Sony WF-1000XM5",
            product_url="https://www.amazon.co.uk/dp/example-uk",
            currency="GBP",
            product_price=Decimal("50"),
            discount_amount=Decimal("51"),
        )
    except ValueError:
        return
    raise AssertionError("Expected discount_amount validation to fail")
