from __future__ import annotations

from typing import Any

from app.connectors.base import BaseConnector, ConnectorHealth
from app.settings import get_settings


class ConnectorRegistry:
    def __init__(self, settings=None):
        self._settings = settings or get_settings()
        self._connectors: dict[str, BaseConnector] = {}

    def register(self, connector: BaseConnector) -> None:
        self._connectors[connector.name] = connector

    def get(self, name: str) -> BaseConnector | None:
        return self._connectors.get(name)

    def all(self) -> list[BaseConnector]:
        return list(self._connectors.values())

    def health_all(self) -> list[ConnectorHealth]:
        return [connector.health() for connector in self._connectors.values()]

    def connectors_for_marketplace(self, marketplace: str) -> list[BaseConnector]:
        if marketplace == "amazon":
            return [c for c in self._connectors.values() if c.platform in {"amazon", "generic"}]
        if marketplace == "shopify":
            return [c for c in self._connectors.values() if c.platform in {"shopify", "supplier", "generic"}]
        return list(self._connectors.values())

    def connectors_for_source(self, source_type: str) -> list[BaseConnector]:
        return [c for c in self._connectors.values() if c.platform == source_type or c.platform == "generic"]


def default_registry() -> ConnectorRegistry:
    from app.connectors.base import UnavailableConnector
    from app.connectors import stubs

    registry = ConnectorRegistry()
    registry.register(UnavailableConnector(name="google_trends", platform="market_research"))
    registry.register(UnavailableConnector(name="tiktok", platform="social"))
    registry.register(UnavailableConnector(name="instagram", platform="social"))
    registry.register(UnavailableConnector(name="youtube_shorts", platform="social"))
    registry.register(UnavailableConnector(name="reddit", platform="social"))
    registry.register(UnavailableConnector(name="amazon", platform="amazon"))
    registry.register(UnavailableConnector(name="walmart", platform="marketplace"))
    registry.register(UnavailableConnector(name="ebay", platform="marketplace"))
    registry.register(UnavailableConnector(name="etsy", platform="marketplace"))
    registry.register(UnavailableConnector(name="google_shopping", platform="marketplace"))
    registry.register(UnavailableConnector(name="cjdropshipping", platform="supplier"))
    registry.register(UnavailableConnector(name="zendrop", platform="supplier"))
    registry.register(UnavailableConnector(name="spocket", platform="supplier"))
    registry.register(UnavailableConnector(name="syncee", platform="supplier"))
    registry.register(UnavailableConnector(name="autods", platform="supplier"))
    registry.register(UnavailableConnector(name="hypersku", platform="supplier"))
    registry.register(UnavailableConnector(name="doba", platform="supplier"))
    return registry
