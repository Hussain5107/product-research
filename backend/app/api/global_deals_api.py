from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import require_access_token
from app.services.global_deals import (
    ExchangeRateInput,
    GlobalOfferInput,
    rank_global_offers,
)

router = APIRouter(prefix="/global-deals", tags=["global-deals"])


class ManualGlobalDealRankingRequest(BaseModel):
    destination: str = Field(default="Abu Dhabi, UAE", min_length=1, max_length=256)
    offers: list[GlobalOfferInput] = Field(min_length=1, max_length=50)
    exchange_rates: list[ExchangeRateInput] = Field(min_length=1, max_length=30)
    max_results: int = Field(default=5, ge=1, le=5)


@router.post("/rank-manual-offers", response_model=dict[str, Any])
async def rank_manual_offers(
    request: ManualGlobalDealRankingRequest,
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    result = rank_global_offers(
        offers=request.offers,
        exchange_rates=request.exchange_rates,
        destination=request.destination,
        max_results=request.max_results,
    )
    return result.model_dump(mode="json")
