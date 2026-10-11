from product_research.data_quality import product_fingerprint, summarize_data_quality
from product_research.models import ProductCandidate, SourceValue, SupplierLead, utc_now_iso
from product_research.profitability import ProfitabilityCalculator


def test_data_quality_separates_verified_estimated_and_missing():
    product = ProductCandidate(
        asin="A1",
        name="Test",
        category="Home",
        marketplace="amazon.ae",
        product_url="https://example.test",
        price=SourceValue(100, "csv", utc_now_iso(), "verified"),
        reviews=SourceValue(10, "csv", utc_now_iso(), "estimated"),
    )
    supplier = SupplierLead("Search", "Alibaba", "https://example.test", None, None, "requires_quote")
    scenarios = ProfitabilityCalculator().calculate(product, [supplier])
    quality = summarize_data_quality(product, [supplier], scenarios)
    assert quality["fingerprint"] == "amazon.ae:a1"
    assert "price" in quality["verified_data"]
    assert "reviews" in quality["estimated_data"]
    assert "verified_supplier_quote" in quality["missing_data"]
    assert "complete_profitability" in quality["missing_data"]


def test_product_fingerprint_is_stable_case_insensitive():
    product = ProductCandidate(
        asin="AbC",
        name="Test",
        category="Home",
        marketplace="Amazon.AE",
        product_url="https://example.test",
        price=SourceValue(100, "csv", utc_now_iso(), "verified"),
    )
    assert product_fingerprint(product) == "amazon.ae:abc"
