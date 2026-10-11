from __future__ import annotations

from typing import Any

from app.connectors.base import BaseConnector, ConnectorCapability, ConnectorHealth


class StubMarketResearchConnector(BaseConnector):
    name: str = "google_trends"
    platform: str = "market_research"

    def _status(self) -> str:
        return "configuration_required"

    def _status_message(self) -> str:
        return "Google Trends connector is not wired yet. Configure access or use alternative trend sources."

    def _capabilities(self) -> list[ConnectorCapability]:
        return [
            ConnectorCapability(name=self.name, status=self._status(), requires_credentials=False, supported_operations=["fetch_trend_observations"]),
        ]

    async def search_products(self, query: str, filters=None, limit=20) -> list[dict[str, Any]]:
        return []

    async def fetch_trend_observations(self, keyword: str, period: str = "30d") -> list[dict[str, Any]]:
        return [
            {
                "source": self.name,
                "keyword": keyword,
                "period": period,
                "data_classification": "unavailable",
                "value_text": "not retrieved",
                "note": "Google Trends connector is not implemented in this build.",
            }
        ]


class StubSocialConnector(BaseConnector):
    name: str = "tiktok"
    platform: str = "social"

    def _status(self) -> str:
        return "unavailable"

    def _status_message(self) -> str:
        return "TikTok research connector is not wired yet."

    def _capabilities(self) -> list[ConnectorCapability]:
        return [
            ConnectorCapability(name=self.name, status=self._status(), requires_credentials=True, supported_operations=["search_products", "fetch_trend_observations"]),
        ]

    async def search_products(self, query: str, filters=None, limit=20) -> list[dict[str, Any]]:
        return []

    async def fetch_trend_observations(self, keyword: str, period: str = "30d") -> list[dict[str, Any]]:
        return [
            {
                "source": self.name,
                "keyword": keyword,
                "period": period,
                "data_classification": "unavailable",
                "value_text": "not retrieved",
                "note": "TikTok connector is not implemented in this build.",
            }
        ]


class StubMarketplaceConnector(BaseConnector):
    name: str = "amazon"
    platform: str = "amazon"

    def _status(self) -> str:
        return "configuration_required"

    def _status_message(self) -> str:
        return "Amazon connector is not wired yet. Authorized access is required to retrieve live listings."

    def _capabilities(self) -> list[ConnectorCapability]:
        return [
            ConnectorCapability(name=self.name, status=self._status(), requires_credentials=True, supported_operations=["search_products", "fetch_product_details"]),
        ]

    async def search_products(self, query: str, filters=None, limit=20) -> list[dict[str, Any]]:
        return []

    async def fetch_product_details(self, identifier: str) -> dict[str, Any] | None:
        return None


class StubSupplierConnector(BaseConnector):
    name: str = "cjdropshipping"
    platform: str = "supplier"

    def _status(self) -> str:
        return "configuration_required"

    def _status_message(self) -> str:
        return "CJdropshipping connector is not wired yet. Add credentials to use supplier search."

    def _capabilities(self) -> list[ConnectorCapability]:
        return [
            ConnectorCapability(name=self.name, status=self._status(), requires_credentials=True, supported_operations=["search_products", "fetch_supplier_products", "fetch_shipping_estimate"]),
        ]

    async def search_products(self, query: str, filters=None, limit=20) -> list[dict[str, Any]]:
        return []

    async def fetch_supplier_products(self, query: str, filters=None, limit=20) -> list[dict[str, Any]]:
        return []

    async def fetch_shipping_estimate(self, supplier_product_id: int | str, destination_zip: str) -> dict[str, Any] | None:
        return None
