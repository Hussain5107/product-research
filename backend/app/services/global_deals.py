from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator


DataClassification = Literal[
    "verified",
    "provider_estimate",
    "model_estimate",
    "user_supplied",
    "unverified",
    "unavailable",
]

VerificationStatus = Literal[
    "checkout_verified",
    "shipping_quote_verified",
    "estimated",
    "incomplete",
]

ComparableStatus = Literal[
    "exact_match",
    "equivalent_regional_version",
    "similar_product",
    "not_comparable",
]


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class ExchangeRateInput(BaseModel):
    from_currency: str = Field(min_length=3, max_length=3)
    to_currency: str = Field(default="AED", min_length=3, max_length=3)
    rate: Decimal = Field(gt=Decimal("0"))
    source_name: str = Field(default="manual")
    source_url: HttpUrl | None = None
    data_classification: DataClassification = "user_supplied"
    retrieved_at: str | None = None

    @field_validator("from_currency", "to_currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()


class GlobalOfferInput(BaseModel):
    marketplace: str = Field(min_length=2, max_length=64)
    product_name: str = Field(min_length=1, max_length=512)
    product_url: HttpUrl
    seller: str | None = Field(default=None, max_length=256)
    condition: str = Field(default="new", max_length=64)
    currency: str = Field(min_length=3, max_length=3)
    product_price: Decimal = Field(ge=Decimal("0"))
    discount_amount: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    shipping_cost: Decimal | None = Field(default=None, ge=Decimal("0"))
    import_charges: Decimal | None = Field(default=None, ge=Decimal("0"))
    taxes: Decimal | None = Field(default=None, ge=Decimal("0"))
    handling: Decimal = Field(default=Decimal("0"), ge=Decimal("0"))
    card_fx_markup_rate: Decimal = Field(default=Decimal("0.0000"), ge=Decimal("0"))
    uae_delivery_eligible: bool | None = None
    delivery_estimate: str | None = None
    comparable_status: ComparableStatus = "similar_product"
    verification_status: VerificationStatus = "incomplete"
    data_classification: DataClassification = "user_supplied"
    evidence_url: HttpUrl | None = None
    evidence_note: str | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        return value.upper()

    @model_validator(mode="after")
    def validate_offer(self) -> "GlobalOfferInput":
        if self.discount_amount > self.product_price:
            raise ValueError("discount_amount cannot exceed product_price")
        return self


class RankedGlobalOffer(BaseModel):
    rank: int | None
    marketplace: str
    product_name: str
    product_url: str
    seller: str | None
    condition: str
    currency: str
    product_price: Decimal
    discount_amount: Decimal
    discounted_price: Decimal
    shipping_cost: Decimal | None
    import_charges: Decimal | None
    taxes: Decimal | None
    handling: Decimal
    currency_conversion_cost: Decimal
    total_delivered_cost: Decimal | None
    total_delivered_cost_aed: Decimal | None
    exchange_rate_to_aed: Decimal
    uae_delivery_eligible: bool | None
    delivery_estimate: str | None
    comparable_status: ComparableStatus
    verification_status: VerificationStatus
    data_classification: DataClassification
    qualifies_for_top_five: bool
    exclusion_reasons: list[str] = Field(default_factory=list)


class GlobalDealRankingResult(BaseModel):
    destination: str = "Abu Dhabi, UAE"
    currency: str = "AED"
    top_offers: list[RankedGlobalOffer]
    similar_or_incomplete_offers: list[RankedGlobalOffer]
    assumptions: list[str]
    warnings: list[str]


def rank_global_offers(
    offers: list[GlobalOfferInput],
    exchange_rates: list[ExchangeRateInput],
    destination: str = "Abu Dhabi, UAE",
    max_results: int = 5,
) -> GlobalDealRankingResult:
    rate_map = {rate.from_currency: rate for rate in exchange_rates if rate.to_currency == "AED"}
    warnings: list[str] = []
    ranked: list[RankedGlobalOffer] = []

    for offer in offers:
        rate = rate_map.get(offer.currency)
        exclusion_reasons = _exclusion_reasons(offer, rate)
        discounted_price = money(offer.product_price - offer.discount_amount)
        known_charges = all(
            charge is not None
            for charge in [offer.shipping_cost, offer.import_charges, offer.taxes]
        )

        if rate is None:
            total_native = None
            fx_cost = Decimal("0.00")
            total_aed = None
            warnings.append(f"Missing AED exchange rate for {offer.currency}.")
        elif not known_charges:
            total_native = None
            fx_cost = Decimal("0.00")
            total_aed = None
        else:
            subtotal = (
                discounted_price
                + offer.shipping_cost
                + offer.import_charges
                + offer.taxes
                + offer.handling
            )
            fx_cost = money(subtotal * offer.card_fx_markup_rate)
            total_native = money(subtotal + fx_cost)
            total_aed = money(total_native * rate.rate)

        ranked.append(
            RankedGlobalOffer(
                rank=None,
                marketplace=offer.marketplace,
                product_name=offer.product_name,
                product_url=str(offer.product_url),
                seller=offer.seller,
                condition=offer.condition,
                currency=offer.currency,
                product_price=money(offer.product_price),
                discount_amount=money(offer.discount_amount),
                discounted_price=discounted_price,
                shipping_cost=money(offer.shipping_cost) if offer.shipping_cost is not None else None,
                import_charges=money(offer.import_charges) if offer.import_charges is not None else None,
                taxes=money(offer.taxes) if offer.taxes is not None else None,
                handling=money(offer.handling),
                currency_conversion_cost=fx_cost,
                total_delivered_cost=total_native,
                total_delivered_cost_aed=total_aed,
                exchange_rate_to_aed=rate.rate if rate else Decimal("0"),
                uae_delivery_eligible=offer.uae_delivery_eligible,
                delivery_estimate=offer.delivery_estimate,
                comparable_status=offer.comparable_status,
                verification_status=offer.verification_status,
                data_classification=offer.data_classification,
                qualifies_for_top_five=not exclusion_reasons,
                exclusion_reasons=exclusion_reasons,
            )
        )

    qualified = sorted(
        [offer for offer in ranked if offer.qualifies_for_top_five],
        key=lambda item: item.total_delivered_cost_aed or Decimal("999999999"),
    )[:max_results]
    for index, offer in enumerate(qualified, start=1):
        offer.rank = index

    qualified_ids = {id(offer) for offer in qualified}
    remainder = [offer for offer in ranked if id(offer) not in qualified_ids]

    return GlobalDealRankingResult(
        destination=destination,
        top_offers=qualified,
        similar_or_incomplete_offers=remainder,
        assumptions=[
            "All arithmetic is deterministic and based only on submitted offer fields.",
            "Shipping, tax, import charge, discount, and exchange-rate values are not inferred when absent.",
            "Only exact or equivalent regional matches with delivery eligibility and complete delivered-cost data qualify for the top five.",
        ],
        warnings=sorted(set(warnings)),
    )


def _exclusion_reasons(offer: GlobalOfferInput, rate: ExchangeRateInput | None) -> list[str]:
    reasons: list[str] = []
    if offer.comparable_status not in {"exact_match", "equivalent_regional_version"}:
        reasons.append("Product is not classified as an exact or equivalent regional match.")
    if offer.uae_delivery_eligible is not True:
        reasons.append("UAE delivery eligibility is not verified.")
    if offer.verification_status == "incomplete":
        reasons.append("Delivered-cost verification is incomplete.")
    if rate is None:
        reasons.append(f"Missing AED exchange rate for {offer.currency}.")
    if offer.shipping_cost is None:
        reasons.append("Shipping cost is unavailable.")
    if offer.import_charges is None:
        reasons.append("Import charges are unavailable.")
    if offer.taxes is None:
        reasons.append("Taxes are unavailable.")
    return reasons
