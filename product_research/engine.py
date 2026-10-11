from __future__ import annotations

from pathlib import Path

from product_research.ai.gemini import GeminiAnalyzer
from product_research.config import ResearchConfig
from product_research.connectors.amazon import AmazonConnector
from product_research.connectors.suppliers import SupplierConnector
from product_research.models import ResearchResult
from product_research.profitability import ProfitabilityCalculator
from product_research.reports import write_reports
from product_research.storage import SupabaseStorage


class ResearchEngine:
    def __init__(self, config: ResearchConfig) -> None:
        self.config = config
        self.amazon = AmazonConnector(config.marketplace)
        self.suppliers = SupplierConnector()
        self.profit = ProfitabilityCalculator()
        self.ai = GeminiAnalyzer(config.gemini_api_key, config.gemini_model)
        self.storage = SupabaseStorage(config.supabase_url, config.supabase_service_role_key)

    def run(self, csv_path: Path | None = None) -> dict[str, object]:
        products = self.amazon.collect(self.config.categories, self.config.products_per_run, csv_path)
        results: list[ResearchResult] = []
        errors: list[str] = []
        for product in products:
            try:
                leads = self.suppliers.find_leads(product)
                scenarios = self.profit.calculate(product, leads)
                analysis = self.ai.analyze(product, leads, scenarios)
                status = "needs_verification" if analysis.data_confidence == "low" else "completed"
                results.append(ResearchResult(product, leads, scenarios, analysis, status))
            except Exception as exc:
                errors.append(f"{product.asin}: {exc}")
        csv_report, xlsx_report = write_reports(results, self.config.report_output_dir)
        run_id = self.storage.save_run(results, "completed_with_errors" if errors else "completed", errors)
        return {
            "products_researched": len(results),
            "errors": errors,
            "csv_report": str(csv_report),
            "xlsx_report": str(xlsx_report),
            "supabase_run_id": run_id,
            "storage_enabled": self.storage.enabled,
        }

