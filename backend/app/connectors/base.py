from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ConnectorCapability(BaseModel):
    name: str
    supported_operations: list[str] = Field(default_factory=list)
    requires_credentials: bool = False
    status: str = "unavailable"
    note: str = ""


class ConnectorHealth(BaseModel):
    connector: str
    status: str
    message: str
    capabilities: list[ConnectorCapability] = Field(default_factory=list)


class BaseConnector(ABC):
    name: str = "base"
    platform: str = "generic"

    def health(self) -> ConnectorHealth:
        return ConnectorHealth(
            connector=self.name,
            status=self._status(),
            message=self._status_message(),
            capabilities=self._capabilities(),
        )

    @abstractmethod
    def _status(self) -> str:
        ...

    @abstractmethod
    def _status_message(self) -> str:
        ...

    @abstractmethod
    def _capabilities(self) -> list[ConnectorCapability]:
        ...

    @abstractmethod
    async def search_products(self, query: str, filters: dict[str, Any] | None = None, limit: int = 20) -> list[dict[str, Any]]:
        ...

    async def fetch_product_details(self, identifier: str) -> dict[str, Any] | None:
        raise NotImplementedError

    async def fetch_trend_observations(self, keyword: str, period: str = "30d") -> list[dict[str, Any]]:
        raise NotImplementedError

    async def fetch_supplier_products(self, query: str, filters: dict[str, Any] | None = None, limit: int = 20) -> list[dict[str, Any]]:
        raise NotImplementedError

    async def fetch_shipping_estimate(self, supplier_product_id: int | str, destination_zip: str) -> dict[str, Any] | None:
        raise NotImplementedError


class UnavailableConnector(BaseConnector):
    name: str = "unavailable"
    platform: str = "generic"

    def __init__(self, name: str | None = None, platform: str | None = None):
        if name is not None:
            self.name = name
        if platform is not None:
            self.platform = platform

    def _status(self) -> str:
        return "unavailable"

    def _status_message(self) -> str:
        return "This connector has not been configured or is not available."

    def _capabilities(self) -> list[ConnectorCapability]:
        return [ConnectorCapability(name=self.name, status="unavailable", note=self._status_message())]

    async def search_products(self, query: str, filters=None, limit=20) -> list[dict[str, Any]]:
        return []

    async def fetch_product_details(self, identifier: str) -> dict[str, Any] | None:
        return None

    async def fetch_trend_observations(self, keyword: str, period: str = "30d") -> list[dict[str, Any]]:
        return []

    async def fetch_supplier_products(self, query: str, filters=None, limit=20) -> list[dict[str, Any]]:
        return []

    async def fetch_shipping_estimate(self, supplier_product_id: int | str, destination_zip: str) -> dict[str, Any] | None:
        return None
