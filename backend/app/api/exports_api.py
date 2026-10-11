from __future__ import annotations

import csv
import io
import json
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_access_token
from app.database import get_db
from app.models.operations import ExportRecord
from app.models.product import Product
from app.models.supplier import Supplier

router = APIRouter(prefix="/exports", tags=["exports"])


@router.get("/download")
async def download_export(
    dataset: str = Query("products", pattern="^(products|suppliers)$"),
    format: str = Query("csv", pattern="^(csv|json|xls|pdf)$"),
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> Response:
    rows = await _dataset_rows(session, dataset)
    filename = f"producthunter-{dataset}.{format}"
    media_type = _media_type(format)

    if format == "json":
        content = json.dumps(rows, indent=2, ensure_ascii=False)
    elif format == "xls":
        content = _spreadsheet_xml(rows)
    elif format == "pdf":
        content = _basic_pdf(f"ProductHunter {dataset.title()} Export", rows)
        media_type = "application/pdf"
        record = ExportRecord(export_type=format, dataset=dataset, filename=filename, row_count=len(rows))
        session.add(record)
        await session.commit()
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    else:
        content = _csv(rows)

    record = ExportRecord(export_type=format, dataset=dataset, filename=filename, row_count=len(rows))
    session.add(record)
    await session.commit()
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/history", response_model=list[dict[str, Any]])
async def export_history(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> list[dict[str, Any]]:
    result = await session.execute(select(ExportRecord).order_by(ExportRecord.created_at.desc()).limit(50))
    return [
        {
            "id": record.id,
            "export_type": record.export_type,
            "dataset": record.dataset,
            "filename": record.filename,
            "status": record.status,
            "row_count": record.row_count,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
        for record in result.scalars().all()
    ]


async def _dataset_rows(session: AsyncSession, dataset: str) -> list[dict[str, Any]]:
    if dataset == "suppliers":
        result = await session.execute(select(Supplier).order_by(Supplier.created_at.desc()))
        return [
            {
                "id": supplier.id,
                "name": supplier.name,
                "platform": supplier.platform,
                "website_url": supplier.website_url,
                "supports_shopify": supplier.supports_shopify,
                "us_warehouse_capable": supplier.us_warehouse_capable,
                "reliability_status": supplier.reliability_status,
                "created_at": supplier.created_at.isoformat() if supplier.created_at else None,
            }
            for supplier in result.scalars().all()
        ]

    result = await session.execute(select(Product).order_by(Product.created_at.desc()))
    return [
        {
            "id": product.id,
            "name": product.name,
            "category": product.category,
            "brand": product.brand,
            "supplier_cost": str(product.supplier_cost),
            "shipping_cost": str(product.shipping_cost),
            "suggested_retail_price": str(product.suggested_retail_price),
            "trend_classification": product.trend_classification,
            "viral_potential": product.viral_potential,
            "competition": product.primary_competition_level,
            "status": product.status,
            "created_at": product.created_at.isoformat() if product.created_at else None,
        }
        for product in result.scalars().all()
    ]


def _csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def _spreadsheet_xml(rows: list[dict[str, Any]]) -> str:
    headers = list(rows[0].keys()) if rows else ["empty"]
    body = []
    body.append('<?xml version="1.0"?>')
    body.append('<?mso-application progid="Excel.Sheet"?>')
    body.append('<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"><Worksheet ss:Name="Export" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"><Table>')
    body.append("<Row>" + "".join(f"<Cell><Data ss:Type=\"String\">{_xml(h)}</Data></Cell>" for h in headers) + "</Row>")
    for row in rows:
        body.append("<Row>" + "".join(f"<Cell><Data ss:Type=\"String\">{_xml(row.get(h, ''))}</Data></Cell>" for h in headers) + "</Row>")
    body.append("</Table></Worksheet></Workbook>")
    return "\n".join(body)


def _basic_pdf(title: str, rows: list[dict[str, Any]]) -> bytes:
    lines = [title, f"Rows: {len(rows)}", ""]
    for row in rows[:40]:
        name = row.get("name") or row.get("display_name") or row.get("id")
        lines.append(str(name)[:90])
    text = "\\n".join(lines).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 760 Td ({text}) Tj ET"
    objects = [
        "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
        "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
        "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj",
        "4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj",
        f"5 0 obj << /Length {len(stream)} >> stream\n{stream}\nendstream endobj",
    ]
    pdf = "%PDF-1.4\n" + "\n".join(objects) + "\ntrailer << /Root 1 0 R >>\n%%EOF"
    return pdf.encode("utf-8")


def _xml(value: Any) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _media_type(format: str) -> str:
    return {
        "csv": "text/csv",
        "json": "application/json",
        "xls": "application/vnd.ms-excel",
        "pdf": "application/pdf",
    }[format]
