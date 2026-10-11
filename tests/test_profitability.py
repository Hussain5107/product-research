from product_research.models import ProductCandidate, SourceValue, SupplierLead, utc_now_iso
from product_research.profitability import ProfitabilityCalculator


def test_profitability_marks_missing_supplier_cost_incomplete():
    product = ProductCandidate(
        asin="A1",
        name="Test product",
        category="Home",
        marketplace="amazon.ae",
        product_url="https://example.test",
        price=SourceValue(100, "test", utc_now_iso(), "verified"),
    )
    scenarios = ProfitabilityCalculator().calculate(product, [])
    assert len(scenarios) == 3
    assert all(item.incomplete_reason == "Missing verified supplier unit cost" for item in scenarios)


def test_profitability_calculates_expected_scenario():
    product = ProductCandidate(
        asin="A1",
        name="Test product",
        category="Home",
        marketplace="amazon.ae",
        product_url="https://example.test",
        price=SourceValue(100, "test", utc_now_iso(), "verified"),
    )
    supplier = SupplierLead("Supplier", "Alibaba", "https://example.test", 25, 100, "verified")
    scenarios = ProfitabilityCalculator().calculate(product, [supplier])
    expected = next(item for item in scenarios if item.name == "expected")
    assert expected.landed_cost == 36.25
    assert expected.profit_per_unit is not None
    assert expected.profit_margin is not None

