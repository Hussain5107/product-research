from __future__ import annotations

import json
import re
import base64
import io
import zipfile
import xml.etree.ElementTree as ET
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.ai.providers import AIORchestrator
from app.api.deps import get_ai_orchestrator, require_access_token

router = APIRouter(prefix="/category-research", tags=["category-research"])


class CategoryResearchRequest(BaseModel):
    category: str = Field(default="Outdoor camping, desert picnic, car camping, and glamping", max_length=240)
    target_market: str = Field(default="UAE and GCC", max_length=120)
    source_market: str = Field(default="China", max_length=80)
    store_platform: str = Field(default="Shopify", max_length=80)
    product_count: int = Field(default=30, ge=10, le=50)
    notes: str | None = Field(default=None, max_length=3000)


class WorkbookImportRequest(BaseModel):
    filename: str = Field(max_length=256)
    content_base64: str = Field(min_length=1)


@router.post("/plan", response_model=dict[str, Any])
async def build_category_research_plan(
    payload: CategoryResearchRequest,
    orchestrator: AIORchestrator = Depends(get_ai_orchestrator),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    base = _deterministic_plan(payload, orchestrator.status())

    if orchestrator.is_configured:
        ai_report = await _ai_category_report(orchestrator, payload, base)
        if ai_report:
            base["ai_report"] = ai_report
            base["report_markdown"] = ai_report.get("report_markdown") or base["report_markdown"]
            base["top_products"] = ai_report.get("top_products") or base["top_products"]
            base["supplier_searches"] = ai_report.get("supplier_searches") or base["supplier_searches"]

    return base


@router.post("/import-workbook", response_model=dict[str, Any])
async def import_category_workbook(
    payload: WorkbookImportRequest,
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    try:
        workbook_bytes = base64.b64decode(payload.content_base64.split(",")[-1])
    except Exception as exc:
        raise ValueError("Invalid workbook upload") from exc

    sheets = _read_xlsx_sheets(workbook_bytes)
    products = _parse_product_scorecard(sheets.get("30 Product Scorecard", []))
    suppliers = _parse_supplier_shortlist(sheets.get("Supplier Shortlist", []))
    economics = _parse_unit_economics(sheets.get("Unit Economics", []))

    return {
        "filename": payload.filename,
        "sheets": [{"name": name, "rows": len(rows)} for name, rows in sheets.items()],
        "products": products,
        "suppliers": suppliers,
        "unit_economics": economics,
        "summary": {
            "product_count": len(products),
            "supplier_count": len(suppliers),
            "economics_count": len(economics),
            "top_product": products[0] if products else None,
            "best_bundle": max(economics, key=lambda row: row.get("contribution_margin", 0), default=None),
        },
    }


def _deterministic_plan(payload: CategoryResearchRequest, ai_status: dict[str, Any]) -> dict[str, Any]:
    products = [
        {
            "name": "Premium inflatable camping sofa with fabric cover",
            "buyer_problem": "Comfortable desert picnic seating without carrying heavy furniture.",
            "uae_angle": "Portable majlis comfort for desert, beach, balcony, and family camping.",
            "score": 7.2,
            "shipping_difficulty": "medium",
            "return_risk": "medium-high",
            "supplier_keywords": ["充气沙发 户外 露营", "inflatable camping sofa fabric cover"],
        },
        {
            "name": "Foldable desert majlis camping chair",
            "buyer_problem": "Low, relaxed seating that fits family picnic and desert setups.",
            "uae_angle": "Majlis-style comfort in a folding portable format.",
            "score": 8.1,
            "shipping_difficulty": "medium",
            "return_risk": "medium",
            "supplier_keywords": ["折叠露营椅 月亮椅", "low folding camping chair"],
        },
        {
            "name": "Rechargeable mini air pump for camping mattresses",
            "buyer_problem": "Inflates sofas, mattresses, and floats without manual effort.",
            "uae_angle": "Small add-on for every camping and beach kit.",
            "score": 8.4,
            "shipping_difficulty": "low-medium",
            "return_risk": "medium",
            "supplier_keywords": ["迷你充气泵 充电 户外", "rechargeable mini air pump camping"],
        },
        {
            "name": "Sand-proof waterproof picnic mat",
            "buyer_problem": "Keeps family seating clean on sand, grass, or beach.",
            "uae_angle": "Desert picnic mat for families and beach trips.",
            "score": 8.0,
            "shipping_difficulty": "low",
            "return_risk": "low",
            "supplier_keywords": ["防沙野餐垫 防水", "sand proof waterproof picnic mat"],
        },
        {
            "name": "Rechargeable camping lantern with power bank",
            "buyer_problem": "Lights the campsite and charges phones.",
            "uae_angle": "Camp lighting for desert nights and power backup.",
            "score": 7.8,
            "shipping_difficulty": "medium",
            "return_risk": "medium",
            "supplier_keywords": ["露营灯 充电 宝", "rechargeable camping lantern power bank"],
        },
        {
            "name": "SUV tailgate shade or awning",
            "buyer_problem": "Creates shade beside the car for beach and desert stops.",
            "uae_angle": "Fast shade for SUV desert trips.",
            "score": 7.5,
            "shipping_difficulty": "high",
            "return_risk": "medium",
            "supplier_keywords": ["车尾帐篷 SUV 天幕", "SUV tailgate awning camping"],
        },
        {
            "name": "Foldable camping table with storage basket",
            "buyer_problem": "Keeps food, stove, and gear organized outdoors.",
            "uae_angle": "Family picnic table for desert and beach setups.",
            "score": 7.4,
            "shipping_difficulty": "medium",
            "return_risk": "low-medium",
            "supplier_keywords": ["折叠露营桌 收纳", "folding camping table storage"],
        },
        {
            "name": "Outdoor storage box and trunk organizer",
            "buyer_problem": "Organizes camping gear in cars and at camp.",
            "uae_angle": "SUV camping organizer for families.",
            "score": 7.0,
            "shipping_difficulty": "medium-high",
            "return_risk": "low",
            "supplier_keywords": ["户外收纳箱 露营", "camping storage box car organizer"],
        },
        {
            "name": "Car/SUV inflatable mattress",
            "buyer_problem": "Turns the back seat or trunk into a sleeping/rest area.",
            "uae_angle": "Comfort rest setup for long desert or road trips.",
            "score": 7.6,
            "shipping_difficulty": "medium",
            "return_risk": "medium-high",
            "supplier_keywords": ["车载充气床 SUV", "SUV inflatable car mattress"],
        },
        {
            "name": "Portable camping shower and water pump",
            "buyer_problem": "Provides water flow for rinsing, cleaning, and camp hygiene.",
            "uae_angle": "Beach, camping, and off-road rinse kit.",
            "score": 7.1,
            "shipping_difficulty": "low-medium",
            "return_risk": "medium",
            "supplier_keywords": ["户外淋浴器 充电 水泵", "portable camping shower pump"],
        },
    ]

    lanes = [
        {
            "name": "UAE demand and price benchmarks",
            "mission": "Check Amazon.ae, Noon, Carrefour, Adventure HQ, Decathlon UAE, Dragon Mart sellers, TikTok, Instagram, and Google Shopping for demand, pricing, reviews, and gaps.",
        },
        {
            "name": "China supplier sourcing",
            "mission": "Search 1688, Alibaba, AliExpress, CJdropshipping, Made-in-China, and sourcing agents for supplier reliability, MOQ, pricing, variants, packaging, and UAE shipping.",
        },
        {
            "name": "Quality and return-risk audit",
            "mission": "Check defect risks such as leaking seams, weak motors, lithium battery compliance, fabric durability, weight capacity, and packaging damage.",
        },
        {
            "name": "Shopify merchandising",
            "mission": "Design collections, bundles, AED pricing tiers, product page proof blocks, FAQs, and upsells for UAE/GCC buyers.",
        },
        {
            "name": "Marketing and content angles",
            "mission": "Find ad hooks, UGC scene ideas, local desert/beach use cases, Arabic/English copy angles, and first test creatives.",
        },
    ]

    supplier_searches = [
        {
            "platform": "1688",
            "query": "充气沙发 户外 露营 牛津布 自动充气",
            "vetting": "Prefer factories with transaction history, real videos, material specs, load rating, packing dimensions, and sample support.",
        },
        {
            "platform": "Alibaba",
            "query": "premium inflatable camping sofa built in pump OEM",
            "vetting": "Look for Verified Supplier, Trade Assurance, export history, MOQ under 100, customization, and UAE shipping quotes.",
        },
        {
            "platform": "1688",
            "query": "迷你充气泵 充电 露营 气垫床",
            "vetting": "Require battery certificates: UN38.3, MSDS, CE/RoHS where applicable, plus clear battery capacity.",
        },
        {
            "platform": "Alibaba",
            "query": "sand proof waterproof picnic mat foldable camping UAE",
            "vetting": "Prioritize lightweight packed size, washable material, neutral colors, custom packaging, and low MOQ.",
        },
    ]

    prompt = _build_copy_prompt(payload)
    markdown = _build_report_markdown(payload, lanes, products, supplier_searches, ai_status, prompt)
    return {
        "status": "ready",
        "ai": ai_status,
        "research_lanes": lanes,
        "top_products": products,
        "supplier_searches": supplier_searches,
        "copy_prompt": prompt,
        "report_markdown": markdown,
        "next_actions": [
            "Run each research lane in a web-capable AI or researcher agent.",
            "Collect 2-5 suppliers per top product and paste supplier evidence into Product Verifier.",
            "Order samples only for products scoring 7/10 or higher after shipping and return-risk checks.",
            "Create Shopify collections around Desert Comfort, Car Camping, Lighting & Power, Mats & Storage, and Water & Cooling.",
        ],
    }


def _read_xlsx_sheets(workbook_bytes: bytes) -> dict[str, list[list[Any]]]:
    ns = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
    }
    sheets: dict[str, list[list[Any]]] = {}
    with zipfile.ZipFile(io.BytesIO(workbook_bytes)) as zf:
        shared_strings = _read_shared_strings(zf, ns)
        workbook = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rel_map = {
            rel.attrib["Id"]: rel.attrib["Target"]
            for rel in rels.findall("pkgrel:Relationship", ns)
        }
        for sheet in workbook.findall("main:sheets/main:sheet", ns):
            name = sheet.attrib.get("name", "Sheet")
            rel_id = sheet.attrib.get(f"{{{ns['rel']}}}id")
            target = rel_map.get(rel_id or "")
            if not target:
                continue
            path = "xl/" + target.lstrip("/")
            if path not in zf.namelist():
                path = "xl/worksheets/" + target.split("/")[-1]
            rows = _read_sheet_rows(zf, path, shared_strings, ns)
            sheets[name] = rows
    return sheets


def _read_shared_strings(zf: zipfile.ZipFile, ns: dict[str, str]) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    strings: list[str] = []
    for si in root.findall("main:si", ns):
        text = "".join(t.text or "" for t in si.findall(".//main:t", ns))
        strings.append(text)
    return strings


def _read_sheet_rows(
    zf: zipfile.ZipFile,
    path: str,
    shared_strings: list[str],
    ns: dict[str, str],
) -> list[list[Any]]:
    root = ET.fromstring(zf.read(path))
    rows: list[list[Any]] = []
    for row in root.findall(".//main:sheetData/main:row", ns):
        values: list[Any] = []
        current_col = 1
        for cell in row.findall("main:c", ns):
            ref = cell.attrib.get("r", "")
            col_index = _column_index(ref)
            while current_col < col_index:
                values.append(None)
                current_col += 1
            values.append(_cell_value(cell, shared_strings, ns))
            current_col += 1
        while values and values[-1] is None:
            values.pop()
        rows.append(values)
    return rows


def _cell_value(cell: ET.Element, shared_strings: list[str], ns: dict[str, str]) -> Any:
    cell_type = cell.attrib.get("t")
    value = cell.find("main:v", ns)
    if value is None or value.text is None:
        inline = cell.find("main:is", ns)
        if inline is not None:
            return "".join(t.text or "" for t in inline.findall(".//main:t", ns))
        return None
    raw = value.text
    if cell_type == "s":
        index = int(raw)
        return shared_strings[index] if 0 <= index < len(shared_strings) else raw
    if cell_type == "b":
        return raw == "1"
    try:
        number = float(raw)
        return int(number) if number.is_integer() else number
    except ValueError:
        return raw


def _column_index(cell_ref: str) -> int:
    letters = re.sub(r"[^A-Z]", "", cell_ref.upper())
    total = 0
    for char in letters:
        total = total * 26 + (ord(char) - ord("A") + 1)
    return total or 1


def _parse_product_scorecard(rows: list[list[Any]]) -> list[dict[str, Any]]:
    header_index = _find_header(rows, "Rank", "Product")
    if header_index is None:
        return []
    headers = [_slug(value) for value in rows[header_index]]
    products: list[dict[str, Any]] = []
    for row in rows[header_index + 1 :]:
        item = _row_dict(headers, row)
        if not item.get("product"):
            continue
        products.append(
            {
                "rank": item.get("rank"),
                "product": item.get("product"),
                "subcategory": item.get("subcategory"),
                "buyer_problem": item.get("buyer_problem"),
                "uae_use_case": item.get("uae_gcc_use_case"),
                "retail_low_aed": item.get("retail_low_aed"),
                "retail_high_aed": item.get("retail_high_aed"),
                "china_buy_low_aed": item.get("china_buy_low_aed"),
                "china_buy_high_aed": item.get("china_buy_high_aed"),
                "shipping": item.get("shipping"),
                "return_risk": item.get("return_risk"),
                "competition": item.get("competition"),
                "differentiation": item.get("differentiation_quality_angle"),
                "ad_hook": item.get("uae_video_ad_hook"),
                "search_leads": " | ".join(
                    str(value)
                    for value in [
                        item.get("alibaba_search_lead"),
                        item.get("1688_search_lead_chinese"),
                        item.get("3rd_platform_search_lead"),
                    ]
                    if value
                )
                or None,
                "supplier_reliability_note": item.get("supplier_reliability_note"),
                "supplier_questions": item.get("questions_for_supplier_sampling"),
                "score": item.get("score_10") or item.get("score"),
                "launch_priority": item.get("launch_recommendation"),
                "compliance_gate": item.get("compliance_or_claims_gate"),
                "evidence_url": item.get("indicative_sourcing_evidence_url"),
            }
        )
    return products


def _parse_supplier_shortlist(rows: list[list[Any]]) -> list[dict[str, Any]]:
    header_index = _find_header(rows, "Outreach tier", "Marketplace supplier")
    if header_index is None:
        return []
    headers = [_slug(value) for value in rows[header_index]]
    suppliers: list[dict[str, Any]] = []
    for row in rows[header_index + 1 :]:
        item = _row_dict(headers, row)
        if not item.get("marketplace_supplier"):
            continue
        suppliers.append(
            {
                "tier": item.get("outreach_tier"),
                "supplier": item.get("marketplace_supplier"),
                "platform": item.get("platform"),
                "best_product_fit": item.get("best_product_fit"),
                "public_signals": item.get("public_listing_signals"),
                "reliability_note": item.get("reliability_key_caveat"),
                "first_inquiry": item.get("first_inquiry_objective"),
                "url": item.get("original_listing_category_url"),
            }
        )
    return suppliers


def _parse_unit_economics(rows: list[list[Any]]) -> list[dict[str, Any]]:
    header_index = _find_header(rows, "Offer / bundle", "Retail incl VAT")
    if header_index is None:
        return []
    headers = [_slug(value) for value in rows[header_index]]
    economics: list[dict[str, Any]] = []
    for row in rows[header_index + 1 :]:
        item = _row_dict(headers, row)
        if not item.get("offer_bundle"):
            continue
        contribution = _number(item.get("contribution_margin"))
        economics.append(
            {
                "offer": item.get("offer_bundle"),
                "retail_incl_vat": item.get("retail_incl_vat"),
                "product_cost": item.get("product_cost"),
                "inbound": item.get("china_uae_inbound"),
                "paid_cac": item.get("paid_cac"),
                "contribution_aed": item.get("contribution_aed"),
                "contribution_margin": contribution,
                "max_break_even_cac": item.get("max_break_even_cac"),
            }
        )
    return economics


def _find_header(rows: list[list[Any]], *required: str) -> int | None:
    needed = {_slug(value) for value in required}
    for index, row in enumerate(rows):
        slugs = {_slug(value) for value in row if value is not None}
        if needed.issubset(slugs):
            return index
    return None


def _row_dict(headers: list[str], row: list[Any]) -> dict[str, Any]:
    return {header: row[index] if index < len(row) else None for index, header in enumerate(headers) if header}


def _slug(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("→", " ")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _number(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value or "0").strip().replace("%", ""))
    except ValueError:
        return 0.0


async def _ai_category_report(
    orchestrator: AIORchestrator,
    payload: CategoryResearchRequest,
    base: dict[str, Any],
) -> dict[str, Any] | None:
    prompt = (
        "Return only JSON. Build a practical category research report for ecommerce sourcing.\n"
        "Do not claim live web results unless user provided them. Use the deterministic starter plan as scaffolding.\n"
        "JSON keys: report_markdown, top_products, supplier_searches.\n\n"
        f"Category: {payload.category}\n"
        f"Target market: {payload.target_market}\n"
        f"Source market: {payload.source_market}\n"
        f"Store platform: {payload.store_platform}\n"
        f"Requested product count: {payload.product_count}\n"
        f"User notes: {payload.notes or ''}\n\n"
        f"Starter plan:\n{json.dumps(base, ensure_ascii=False)[:12000]}"
    )
    try:
        text = await orchestrator.chat_completion([{"role": "user", "content": prompt}], temperature=0.2, max_tokens=5000)
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
            cleaned = re.sub(r"```$", "", cleaned).strip()
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def _build_copy_prompt(payload: CategoryResearchRequest) -> str:
    return f"""You are my ecommerce category research team.

Goal:
Research {payload.category} for a {payload.store_platform} store targeting {payload.target_market}. Source products mainly from {payload.source_market}.

Work like multiple focused researcher agents. Split the work into:
1. UAE/GCC demand, seasonality, and price benchmarks.
2. China supplier sourcing on 1688, Alibaba, AliExpress, CJdropshipping, and Made-in-China.
3. Product quality, compliance, shipping, and return-risk checks.
4. Shopify merchandising, collections, bundles, and AED pricing.
5. UAE/GCC ad hooks and content strategy.

For each product idea collect:
- Product name
- Buyer problem
- UAE/GCC use case
- Suggested AED retail price
- Estimated China sourcing cost
- Shipping difficulty
- Return risk
- Competition level
- Differentiation angle
- Ad hook
- 2-5 supplier links or search leads
- Supplier reliability notes
- Questions to ask before ordering samples
- Score out of 10

Be strict. Avoid products that are too bulky, fragile, dangerous, regulated, poor quality, or impossible to differentiate.

Final output:
1. Category overview
2. Top product subcategories
3. Top {payload.product_count} product ideas
4. Top 10 highest-potential products
5. Supplier shortlist
6. Products to avoid
7. Shopify collections
8. AED pricing strategy
9. Bundle ideas
10. UAE marketing hooks
11. First 5 products to test
12. First suppliers to contact
13. Supplier questions

User notes:
{payload.notes or "No extra notes."}
"""


def _build_report_markdown(
    payload: CategoryResearchRequest,
    lanes: list[dict[str, str]],
    products: list[dict[str, Any]],
    supplier_searches: list[dict[str, str]],
    ai_status: dict[str, Any],
    prompt: str,
) -> str:
    lane_lines = "\n".join([f"- **{lane['name']}**: {lane['mission']}" for lane in lanes])
    product_lines = "\n".join(
        [
            f"- **{p['name']}** ({p['score']}/10): {p['uae_angle']} Shipping: {p['shipping_difficulty']}. Return risk: {p['return_risk']}."
            for p in products
        ]
    )
    supplier_lines = "\n".join(
        [f"- **{s['platform']}**: `{s['query']}`. {s['vetting']}" for s in supplier_searches]
    )
    return f"""# Category Research Plan

**Category:** {payload.category}
**Target market:** {payload.target_market}
**Source market:** {payload.source_market}
**Store platform:** {payload.store_platform}
**AI configured:** {ai_status.get("configured")}

## Research Lanes
{lane_lines}

## Starter Product Shortlist
{product_lines}

## Supplier Search Leads
{supplier_lines}

## First Shopify Collections
- Desert Comfort
- Car Camping
- Lighting & Power
- Mats & Storage
- Water & Cooling
- Glamping Setup

## First Test Rule
Start only with products that are compact enough to ship, have clear material specs, have supplier videos, and can be positioned for UAE desert/beach/family use.

## Copy Prompt
```text
{prompt}
```
"""
