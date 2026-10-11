from __future__ import annotations

from dataclasses import asdict
from typing import Any

from product_research.models import ResearchResult, utc_now_iso


class SupabaseStorage:
    def __init__(self, url: str | None, service_role_key: str | None) -> None:
        self.enabled = bool(url and service_role_key)
        self.client = None
        if self.enabled:
            from supabase import create_client

            self.client = create_client(url, service_role_key)

    def save_run(self, results: list[ResearchResult], status: str, errors: list[str]) -> str | None:
        if not self.enabled or self.client is None:
            return None
        run_payload: dict[str, Any] = {
            "started_at": utc_now_iso(),
            "completed_at": utc_now_iso(),
            "status": status,
            "products_researched": len(results),
            "successful_analyses": sum(1 for item in results if item.status == "completed"),
            "errors": errors,
        }
        run = self.client.table("research_runs").insert(run_payload).execute()
        run_id = run.data[0]["id"]
        for result in results:
            self._save_result(run_id, result)
        return run_id

    def _save_result(self, run_id: str, result: ResearchResult) -> None:
        assert self.client is not None
        product_payload = {
            "asin": result.product.asin,
            "marketplace": result.product.marketplace,
            "name": result.product.name,
            "category": result.product.category,
            "product_url": result.product.product_url,
            "latest_price": result.product.price.value,
            "data": asdict(result.product),
        }
        product = self.client.table("products").upsert(product_payload, on_conflict="marketplace,asin").execute()
        product_id = product.data[0]["id"]
        self.client.table("product_price_history").insert({
            "product_id": product_id,
            "price": result.product.price.value,
            "source": result.product.price.source,
            "verification_status": result.product.price.verification_status,
            "collected_at": result.product.price.collected_at,
        }).execute()
        for lead in result.suppliers:
            self.client.table("suppliers").insert({
                "product_id": product_id,
                "supplier_name": lead.supplier_name,
                "platform": lead.platform,
                "product_link": lead.product_link,
                "unit_purchase_price": lead.unit_purchase_price,
                "minimum_order_quantity": lead.minimum_order_quantity,
                "verification_status": lead.verification_status,
                "notes": lead.notes,
                "data": asdict(lead),
            }).execute()
        self.client.table("research_results").insert({
            "research_run_id": run_id,
            "product_id": product_id,
            "opportunity_score": result.ai_analysis.opportunity_score,
            "data_confidence": result.ai_analysis.data_confidence,
            "analysis": asdict(result.ai_analysis),
            "status": result.status,
        }).execute()
        self.client.table("profit_calculations").insert({
            "research_run_id": run_id,
            "product_id": product_id,
            "scenarios": [asdict(item) for item in result.profit_scenarios],
        }).execute()

