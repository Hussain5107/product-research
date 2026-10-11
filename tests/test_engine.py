from product_research.config import ResearchConfig
from product_research.engine import ResearchEngine


def test_engine_runs_with_sample_data(tmp_path):
    config = ResearchConfig(
        gemini_api_key=None,
        gemini_model="gemini-1.5-flash",
        supabase_url=None,
        supabase_service_role_key=None,
        mode="sample",
        marketplace="amazon.ae",
        products_per_run=2,
        categories=["Outdoor camping", "Home and kitchen"],
        report_output_dir=tmp_path,
    )
    result = ResearchEngine(config).run()
    assert result["products_researched"] == 2
    assert result["errors"] == []
    assert (tmp_path / "daily_product_research_report.csv").exists()
    assert (tmp_path / "daily_product_research_report.xlsx").exists()

