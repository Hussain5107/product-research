from __future__ import annotations

import csv
from pathlib import Path

from product_research.models import ProductCandidate, SourceValue, utc_now_iso


class AmazonConnector:
    """Connector facade that avoids unauthorized scraping.

    Live Amazon integrations should use official APIs or authorized providers.
    Until those are configured, this connector supports CSV and bundled sample data.
    """

    def __init__(self, marketplace: str) -> None:
        self.marketplace = marketplace

    def collect(self, categories: list[str], limit: int, csv_path: Path | None = None) -> list[ProductCandidate]:
        if csv_path:
            return self._from_csv(csv_path, limit)
        return self._sample_products(categories, limit)

    def _from_csv(self, path: Path, limit: int) -> list[ProductCandidate]:
        products: list[ProductCandidate] = []
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if len(products) >= limit:
                    break
                products.append(
                    ProductCandidate(
                        asin=row.get("asin", "").strip() or f"CSV-{len(products)+1}",
                        name=row["name"].strip(),
                        category=row.get("category", "Uncategorized").strip(),
                        marketplace=self.marketplace,
                        product_url=row.get("product_url", "").strip(),
                        price=SourceValue(float(row["price"]), f"csv:{path.name}", utc_now_iso(), "verified", "high"),
                        reviews=_optional_source(row, "reviews", path.name),
                        rating=_optional_source(row, "rating", path.name),
                        bsr=_optional_source(row, "bsr", path.name),
                    )
                )
        return products

    def _sample_products(self, categories: list[str], limit: int) -> list[ProductCandidate]:
        seed = [
            ("SAMPLE-CAMP-001", "Compact desert camping lantern", "Outdoor camping", 89.0, 214, 4.4),
            ("SAMPLE-PICNIC-001", "Foldable insulated picnic basket", "Desert picnic accessories", 119.0, 86, 4.2),
            ("SAMPLE-CAR-001", "Car seat gap organizer with cup holder", "Car accessories", 59.0, 428, 4.1),
            ("SAMPLE-HOME-001", "Stackable kitchen storage containers", "Home and kitchen", 74.0, 512, 4.5),
            ("SAMPLE-STORAGE-001", "Under-bed storage bags set", "Storage and organization", 49.0, 137, 4.0),
        ]
        selected_categories = set(categories)
        products = []
        for asin, name, category, price, reviews, rating in seed:
            if category not in selected_categories:
                continue
            products.append(
                ProductCandidate(
                    asin=asin,
                    name=name,
                    category=category,
                    marketplace=self.marketplace,
                    product_url=f"https://www.amazon.ae/dp/{asin}",
                    price=SourceValue(price, "sample_fixture", utc_now_iso(), "estimated", "medium"),
                    reviews=SourceValue(reviews, "sample_fixture", utc_now_iso(), "estimated", "medium"),
                    rating=SourceValue(rating, "sample_fixture", utc_now_iso(), "estimated", "medium"),
                    sales_estimate=SourceValue(None, "not_configured", utc_now_iso(), "missing", "low"),
                )
            )
            if len(products) >= limit:
                break
        return products


def _optional_source(row: dict[str, str], field: str, source_name: str) -> SourceValue | None:
    value = row.get(field, "").strip()
    if not value:
        return None
    parsed = float(value) if "." in value else int(value)
    return SourceValue(parsed, f"csv:{source_name}", utc_now_iso(), "verified", "high")

