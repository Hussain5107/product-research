from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from app.api.category_research_api import (
    CategoryResearchRequest,
    _deterministic_plan,
    _parse_product_scorecard,
    _parse_supplier_shortlist,
    _parse_unit_economics,
    _read_xlsx_sheets,
)
import base64


class CategoryAgentHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def handle_expect_100(self) -> bool:
        self.send_response_only(100)
        self.end_headers()
        return True

    def do_OPTIONS(self) -> None:
        self._send_json({})

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"status": "ok", "mode": "category-agent-standalone"})
            return
        self._send_json({"detail": "Not Found"}, status=404)

    def do_POST(self) -> None:
        try:
            print(f"POST {self.path} length={self.headers.get('Content-Length')}", flush=True)
            payload = self._read_json()
            if self.path == "/category-research/plan":
                request = CategoryResearchRequest.model_validate(payload)
                result = _deterministic_plan(
                    request,
                {
                        "configured": False,
                        "provider": "standalone",
                        "model": "deterministic",
                        "message": "Standalone category agent API is running locally.",
                    },
                )
                self._send_json(result)
                return

            if self.path == "/category-research/import-workbook":
                content = str(payload.get("content_base64") or "")
                workbook_bytes = base64.b64decode(content.split(",")[-1])
                print(f"decoded workbook bytes={len(workbook_bytes)}", flush=True)
                sheets = _read_xlsx_sheets(workbook_bytes)
                products = _parse_product_scorecard(sheets.get("30 Product Scorecard", []))
                suppliers = _parse_supplier_shortlist(sheets.get("Supplier Shortlist", []))
                economics = _parse_unit_economics(sheets.get("Unit Economics", []))
                self._send_json(
                    {
                        "filename": payload.get("filename"),
                        "sheets": [{"name": name, "rows": len(rows)} for name, rows in sheets.items()],
                        "products": products,
                        "suppliers": suppliers,
                        "unit_economics": economics,
                        "summary": {
                            "product_count": len(products),
                            "supplier_count": len(suppliers),
                            "economics_count": len(economics),
                            "top_product": products[0] if products else None,
                            "best_bundle": max(
                                economics,
                                key=lambda row: row.get("contribution_margin", 0),
                                default=None,
                            ),
                        },
                    }
                )
                return

            self._send_json({"detail": "Not Found"}, status=404)
        except Exception as exc:
            print(f"request failed: {exc!r}", flush=True)
            self._send_json({"detail": f"{exc.__class__.__name__}: {exc}"}, status=500)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length == 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw) if raw else {}

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8000), CategoryAgentHandler)
    print("Category agent standalone API listening on http://127.0.0.1:8000", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
