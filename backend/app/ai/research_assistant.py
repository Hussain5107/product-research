from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.ai.providers import AIORchestrator


class ProductSnapshotForAI(BaseModel):
    name: str = ""
    description: str = ""
    category: str = ""
    brand: str = ""
    asin: str = ""
    product_url: str = ""
    supplier_cost: str = ""
    shipping_cost: str = ""
    suggested_retail_price: str = ""
    us_warehouse_verified: bool = False
    us_warehouse_verification_status: str = "unverified"
    estimated_delivery_days: str = ""
    trend_classification: str = "insufficient_evidence"
    viral_potential: str = "low"
    primary_competition_level: str = "unknown"
    amazon_fulfillment_suitable: str = "needs_review"
    sources: list[dict[str, str]] = Field(default_factory=list)
    competitors: list[dict[str, str]] = Field(default_factory=list)
    observations: list[dict[str, str]] = Field(default_factory=list)
    ai_provider_configured: bool = False
    ai_status: str = ""


class ClassificationRequest(BaseModel):
    snapshot: ProductSnapshotForAI
    marketplace: str = "shopify"


class ClassificationResponse(BaseModel):
    opportunity_classification: str = "insufficient_evidence"
    verdict: str = ""
    reasoning: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    recommended_next_action: str = ""


class MarketingPlanRequest(BaseModel):
    snapshot: ProductSnapshotForAI
    marketplace: str = "shopify"


class MarketingPlanResponse(BaseModel):
    target_audience: list[str] = Field(default_factory=list)
    pain_points: list[str] = Field(default_factory=list)
    video_hooks: list[str] = Field(default_factory=list)
    video_concepts: list[dict[str, str]] = Field(default_factory=list)
    product_positioning: str = ""
    bundles: list[str] = Field(default_factory=list)
    upsells: list[str] = Field(default_factory=list)


class AmazonSuitabilityRequest(BaseModel):
    snapshot: ProductSnapshotForAI
    marketplace: str = "amazon"


class AmazonSuitabilityResponse(BaseModel):
    suitability: str = "needs_review"
    advantages: list[str] = Field(default_factory=list)
    restrictions_or_risks: list[str] = Field(default_factory=list)
    compliance_note: str = ""
    recommended_action: str = ""


class RecommendationRequest(BaseModel):
    products: list[ProductSnapshotForAI]
    marketplace: str = "shopify"


class RecommendationResponse(BaseModel):
    recommended_product_index: int = -1
    reason: str = ""
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    conditions_that_change_recommendation: list[str] = Field(default_factory=list)


def _build_messages(system: str, user: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


SYSTEM_CLASSIFICATION = """You are a commercial product research analyst assistant for Amazon USA and Shopify USA.

Your job is to classify a product opportunity using the provided snapshot.

Rules:
- Base your answer only on the information provided.
- If important information is missing, say so clearly.
- Do not invent sales, supplier stock, prices, or links.
- Financials may be included in the snapshot but should be treated as user-supplied or estimated unless marked otherwise.
- Return valid JSON only.
"""


USER_CLASSIFICATION = """Classify this product.

Marketplace: {marketplace}

Snapshot:
{json}

Respond with JSON:
{{
  "opportunity_classification": "strong_candidate" | "promising_test_required" | "monitor" | "high_risk" | "reject" | "insufficient_evidence",
  "verdict": "short commercial assessment",
  "reasoning": ["...", "..."],
  "missing_information": ["...", "..."],
  "recommended_next_action": "sample / verify supplier / recheck competition / reject / monitor"
}}
"""


SYSTEM_MARKETING = """You are a social media marketing strategist for e-commerce products.

Your job is to propose marketing angles for a product that can be demonstrated in short-form video.

Rules:
- Do not recommend copying competitor videos or assets without permission.
- Base ideas on the product snapshot.
- Focus on authentic demonstration and legitimate creator partnerships.
- Return valid JSON only.
"""


USER_MARKETING = """Create a marketing plan for this product.

Marketplace: {marketplace}

Snapshot:
{json}

Respond with JSON:
{{
  "target_audience": ["...", "..."],
  "pain_points": ["...", "..."],
  "video_hooks": ["first 3 seconds hook", "..."],
  "video_concepts": [{"platform": "tiktok", "concept": "..."}, {"platform": "instagram", "concept": "..."}],
  "product_positioning": ".",
  "bundles": ["...", "..."],
  "upsells": ["...", "..."]
}}
"""


SYSTEM_AMAZON = """You are an Amazon marketplace compliance and suitability assistant.

Your job is to assess whether a product seems suitable for Amazon based on the snapshot.

Rules:
- Do not assert full compliance without evidence.
- Flag areas that require further review.
- Return valid JSON only.
"""


USER_AMAZON = """Assess Amazon suitability for this product.

Snapshot:
{json}

Respond with JSON:
{{
  "suitability": "suitable" | "needs_review" | "likely_unsuitable",
  "advantages": ["...", "..."],
  "restrictions_or_risks": ["...", "..."],
  "compliance_note": ".",
  "recommended_action": "review category restrictions / verify certifications / proceed with caution / reject"
}}
"""


SYSTEM_RECOMMEND = """You are a product selection assistant.

You are comparing several product snapshots for a marketplace.

Rules:
- Do not fabricate facts.
- Choose the strongest candidate based on the visible evidence and explain why.
- Note conditions that could change the recommendation.
- Return valid JSON only.
"""


USER_RECOMMEND = """Choose the best product for {marketplace}.

Products:
{numbered}

Respond with JSON:
{{
  "recommended_product_index": 0,
  "reason": ".",
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "conditions_that_change_recommendation": ["...", "..."]
}}
"""


async def classify_product(
    orchestrator: AIORchestrator,
    request: ClassificationRequest,
) -> ClassificationResponse:
    if not orchestrator.is_configured:
        return ClassificationResponse(
            opportunity_classification="insufficient_evidence",
            verdict="AI provider not configured. Classification not available.",
            reasoning=["The AI provider has not been configured in the backend."],
            missing_information=["AI provider"],
            recommended_next_action="Configure AI provider or review manually",
        )

    snapshot = request.snapshot
    user_json = snapshot.model_dump_json(indent=2)
    messages = _build_messages(
        SYSTEM_CLASSIFICATION,
        USER_CLASSIFICATION.format(
            marketplace=request.marketplace,
            json=user_json,
        ),
    )
    try:
        raw = await orchestrator.chat_completion(messages, temperature=0.2, max_tokens=1200)
        return ClassificationResponse.model_validate_json(raw)
    except Exception as e:
        return ClassificationResponse(
            opportunity_classification="insufficient_evidence",
            verdict="AI classification failed.",
            reasoning=[f"AI error: {e}"],
            missing_information=["AI response"],
            recommended_next_action="Retry or classify manually",
        )


async def generate_marketing_plan(
    orchestrator: AIORchestrator,
    request: MarketingPlanRequest,
) -> MarketingPlanResponse:
    if not orchestrator.is_configured:
        return MarketingPlanResponse(
            target_audience=["AI provider not configured"],
            pain_points=["AI provider not configured"],
            video_hooks=["Configure AI provider to generate marketing ideas"],
            video_concepts=[{"platform": "tiktok", "concept": "AI provider not configured"}],
            product_positioning="",
            bundles=[],
            upsells=[],
        )

    snapshot = request.snapshot
    user_json = snapshot.model_dump_json(indent=2)
    messages = _build_messages(
        SYSTEM_MARKETING,
        USER_MARKETING.format(
            marketplace=request.marketplace,
            json=user_json,
        ),
    )
    try:
        raw = await orchestrator.chat_completion(messages, temperature=0.4, max_tokens=1600)
        return MarketingPlanResponse.model_validate_json(raw)
    except Exception as e:
        return MarketingPlanResponse(
            target_audience=["AI generation failed"],
            pain_points=["AI generation failed"],
            video_hooks=[f"AI error: {e}"],
            video_concepts=[{"platform": "tiktok", "concept": "AI generation failed"}],
            product_positioning="",
            bundles=[],
            upsells=[],
        )


async def assess_amazon_suitability(
    orchestrator: AIORchestrator,
    request: AmazonSuitabilityRequest,
) -> AmazonSuitabilityResponse:
    if not orchestrator.is_configured:
        return AmazonSuitabilityResponse(
            suitability="needs_review",
            advantages=["AI provider not configured"],
            restrictions_or_risks=["AI provider not configured"],
            compliance_note="AI provider not configured. Review manually.",
            recommended_action="Configure AI provider or review manually",
        )

    snapshot = request.snapshot
    user_json = snapshot.model_dump_json(indent=2)
    messages = _build_messages(
        SYSTEM_AMAZON,
        USER_AMAZON.format(json=user_json),
    )
    try:
        raw = await orchestrator.chat_completion(messages, temperature=0.2, max_tokens=1400)
        return AmazonSuitabilityResponse.model_validate_json(raw)
    except Exception as e:
        return AmazonSuitabilityResponse(
            suitability="needs_review",
            advantages=["AI assessment failed"],
            restrictions_or_risks=[f"AI error: {e}"],
            compliance_note="AI assessment failed. Review manually.",
            recommended_action="Retry or review manually",
        )


async def recommend_product(
    orchestrator: AIORchestrator,
    request: RecommendationRequest,
) -> RecommendationResponse:
    if not orchestrator.is_configured:
        return RecommendationResponse(
            recommended_product_index=-1,
            reason="AI provider not configured. Recommendation not available.",
            strengths=["AI provider not configured"],
            weaknesses=["AI provider not configured"],
            conditions_that_change_recommendation=["Configure AI provider"],
        )

    products = request.products
    if not products:
        return RecommendationResponse(
            recommended_product_index=-1,
            reason="No products provided.",
            strengths=["None provided"],
            weaknesses=["None provided"],
            conditions_that_change_recommendation=["Provide products"],
        )

    numbered = ""
    for idx, product in enumerate(products, start=1):
        numbered += f"\n{idx}. {product.name}\n{json.dumps(product.model_dump(exclude_none=True), indent=2)}\n"

    user_json = USER_RECOMMEND.format(
        marketplace=request.marketplace,
        numbered=numbered,
    )
    messages = _build_messages(SYSTEM_RECOMMEND, user_json)
    try:
        raw = await orchestrator.chat_completion(messages, temperature=0.3, max_tokens=1600)
        return RecommendationResponse.model_validate_json(raw)
    except Exception as e:
        return RecommendationResponse(
            recommended_product_index=-1,
            reason=f"AI recommendation failed: {e}",
            strengths=["AI generation failed"],
            weaknesses=["AI generation failed"],
            conditions_that_change_recommendation=["Retry"],
        )
