from __future__ import annotations

import csv
from dataclasses import asdict
from pathlib import Path

from openpyxl import Workbook

from product_research.models import ResearchResult


def write_reports(results: list[ResearchResult], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "daily_product_research_report.csv"
    xlsx_path = output_dir / "daily_product_research_report.xlsx"
    rows = [_row(result) for result in results]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["status"])
        writer.writeheader()
        writer.writerows(rows)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Research Report"
    if rows:
        sheet.append(list(rows[0].keys()))
        for row in rows:
            sheet.append(list(row.values()))
    else:
        sheet.append(["status"])
        sheet.append(["No products researched"])
    workbook.save(xlsx_path)
    return csv_path, xlsx_path


def _row(result: ResearchResult) -> dict[str, object]:
    expected = next((item for item in result.profit_scenarios if item.name == "expected"), None)
    return {
        "asin": result.product.asin,
        "product": result.product.name,
        "category": result.product.category,
        "marketplace": result.product.marketplace,
        "price": result.product.price.value,
        "price_source": result.product.price.source,
        "opportunity_score": result.ai_analysis.opportunity_score,
        "data_confidence": result.ai_analysis.data_confidence,
        "expected_profit_margin": expected.profit_margin if expected else None,
        "profit_status": expected.incomplete_reason if expected else "missing",
        "status": result.status,
        "risks": "; ".join(result.ai_analysis.main_risks),
        "recommended_actions": "; ".join(result.ai_analysis.recommended_next_actions),
    }

