from __future__ import annotations

import json
from typing import Any

import jsonschema

from product_research.models import AiAnalysis, ProductCandidate, ProfitScenario, SupplierLead


ANALYSIS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "opportunity_score",
        "data_confidence",
        "demand_assessment",
        "competition_assessment",
        "profitability_assessment",
        "differentiation_recommendations",
        "main_risks",
        "recommended_next_actions",
        "verification_notes",
    ],
    "properties": {
        "opportunity_score": {"type": "number", "minimum": 0, "maximum": 10},
        "data_confidence": {"type": "string", "enum": ["low", "medium", "high"]},
        "demand_assessment": {"type": "string"},
        "competition_assessment": {"type": "string"},
        "profitability_assessment": {"type": "string"},
        "differentiation_recommendations": {"type": "array", "items": {"type": "string"}},
        "main_risks": {"type": "array", "items": {"type": "string"}},
        "recommended_next_actions": {"type": "array", "items": {"type": "string"}},
        "verification_notes": {"type": "array", "items": {"type": "string"}},
    },
}


class GeminiAnalyzer:
    def __init__(self, api_key: str | None, model_name: str) -> None:
        self.api_key = api_key
        self.model_name = model_name

    def analyze(self, product: ProductCandidate, suppliers: list[SupplierLead], profit: list[ProfitScenario]) -> AiAnalysis:
        if not self.api_key:
            return self._fallback(product, profit, "Gemini API key is not configured")
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(self._prompt(product, suppliers, profit))
            text = (response.text or "").strip()
            if text.startswith("```"):
                text = text.strip("`").removeprefix("json").strip()
            payload = json.loads(text)
            jsonschema.validate(payload, ANALYSIS_SCHEMA)
            return AiAnalysis(raw=payload, **payload)
        except Exception as exc:  # Keep automation running on quota/API/schema failures.
            return self._fallback(product, profit, f"Gemini unavailable: {exc.__class__.__name__}")

    def _prompt(self, product: ProductCandidate, suppliers: list[SupplierLead], profit: list[ProfitScenario]) -> str:
        return (
            "Analyze this Amazon product opportunity using only the supplied data. "
            "Do not invent sales, prices, reviews, supplier quotes, fees, or rankings. "
            "Return strict JSON matching this schema: "
            f"{json.dumps(ANALYSIS_SCHEMA)}\n\n"
            f"Product: {json.dumps(product, default=lambda o: getattr(o, '__dict__', str(o)))}\n"
            f"Supplier leads: {json.dumps(suppliers, default=lambda o: getattr(o, '__dict__', str(o)))}\n"
            f"Profit scenarios: {json.dumps(profit, default=lambda o: getattr(o, '__dict__', str(o)))}"
        )

    def _fallback(self, product: ProductCandidate, profit: list[ProfitScenario], reason: str) -> AiAnalysis:
        has_complete_profit = any(item.profit_margin is not None for item in profit)
        score = 4.0 if not has_complete_profit else 6.0
        return AiAnalysis(
            opportunity_score=score,
            data_confidence="low" if not has_complete_profit else "medium",
            demand_assessment="Demand cannot be verified without an authorized Amazon data source.",
            competition_assessment="Competition is unknown until seller and ranking data are connected.",
            profitability_assessment="Profitability is incomplete without verified supplier quotations." if not has_complete_profit else "Profitability calculated from configured assumptions.",
            differentiation_recommendations=["Collect verified review complaints before defining differentiation."],
            main_risks=["Missing verified supplier cost", "Marketplace data source not configured", reason],
            recommended_next_actions=["Import verified Amazon data by CSV or connect an authorized provider", "Request supplier quotations"],
            verification_notes=[reason, f"Input price source: {product.price.source}", f"Input price status: {product.price.verification_status}"],
            raw={"fallback": True, "reason": reason},
        )

