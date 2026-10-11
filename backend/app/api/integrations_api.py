from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import require_access_token
from app.connectors.registry import default_registry
from app.database import get_db
from app.models.core import utc_now
from app.models.operations import ConnectorConfig

router = APIRouter(prefix="/integrations", tags=["integrations"])


class ConnectorConfigUpsert(BaseModel):
    name: str = Field(max_length=128)
    display_name: str = Field(max_length=256)
    connector_type: str = Field(default="marketplace", max_length=64)
    status: str = Field(default="configured", max_length=32)
    base_url: str | None = Field(default=None, max_length=2048)
    api_key: str | None = None
    notes: str | None = None
    is_enabled: bool = True


@router.get("/health", response_model=list[dict[str, Any]])
async def integrations_health(
    _access: None = Depends(require_access_token),
) -> list[dict[str, Any]]:
    registry = default_registry()
    return [
        {
            "name": h.connector,
            "platform": h.status,
            "status": h.status,
            "message": h.message,
            "capabilities": [c.model_dump() for c in h.capabilities],
        }
        for h in registry.health_all()
    ]


@router.get("/configs", response_model=list[dict[str, Any]])
async def list_connector_configs(
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> list[dict[str, Any]]:
    await _seed_default_connectors(session)
    result = await session.execute(select(ConnectorConfig).order_by(ConnectorConfig.display_name))
    return [_serialize_config(config) for config in result.scalars().all()]


@router.put("/configs", response_model=dict[str, Any])
async def save_connector_config(
    payload: ConnectorConfigUpsert,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    result = await session.execute(select(ConnectorConfig).where(ConnectorConfig.name == payload.name))
    config = result.scalar_one_or_none()
    if config is None:
        config = ConnectorConfig(
            name=payload.name,
            display_name=payload.display_name,
            connector_type=payload.connector_type,
        )
        session.add(config)

    config.display_name = payload.display_name
    config.connector_type = payload.connector_type
    config.status = payload.status
    config.base_url = payload.base_url
    if payload.api_key:
        config.api_key = payload.api_key
    config.notes = payload.notes
    config.is_enabled = payload.is_enabled
    config.last_checked_at = utc_now()
    await session.commit()
    await session.refresh(config)
    return _serialize_config(config)


@router.post("/configs/{name}/check", response_model=dict[str, Any])
async def check_connector_config(
    name: str,
    session: AsyncSession = Depends(get_db),
    _access: None = Depends(require_access_token),
) -> dict[str, Any]:
    result = await session.execute(select(ConnectorConfig).where(ConnectorConfig.name == name))
    config = result.scalar_one_or_none()
    if config is None:
        return {"name": name, "status": "missing", "message": "Connector is not configured."}
    config.last_checked_at = utc_now()
    config.status = "configured" if config.is_enabled else "disabled"
    await session.commit()
    return {
        "name": config.name,
        "status": config.status,
        "message": "Configuration saved. Live retrieval requires the provider's compliant API access.",
    }


async def _seed_default_connectors(session: AsyncSession) -> None:
    defaults = [
        ("amazon_best_sellers", "Amazon Best Sellers", "marketplace"),
        ("google_trends", "Google Trends", "demand"),
        ("cjdropshipping", "CJdropshipping", "supplier"),
        ("zendrop", "Zendrop", "supplier"),
        ("spocket", "Spocket", "supplier"),
        ("syncee", "Syncee", "supplier"),
        ("tiktok_shop", "TikTok Shop", "social"),
        ("reddit", "Reddit", "community"),
        ("product_discovery_web", "Product Discovery Websites", "web"),
    ]
    changed = False
    for name, display_name, connector_type in defaults:
        existing = await session.execute(select(ConnectorConfig).where(ConnectorConfig.name == name))
        if existing.scalar_one_or_none() is None:
            session.add(
                ConnectorConfig(
                    name=name,
                    display_name=display_name,
                    connector_type=connector_type,
                    status="planned",
                    is_enabled=False,
                )
            )
            changed = True
    if changed:
        await session.commit()


def _serialize_config(config: ConnectorConfig) -> dict[str, Any]:
    return {
        "id": config.id,
        "name": config.name,
        "display_name": config.display_name,
        "connector_type": config.connector_type,
        "status": config.status,
        "base_url": config.base_url,
        "api_key_configured": bool(config.api_key),
        "notes": config.notes,
        "is_enabled": config.is_enabled,
        "last_checked_at": config.last_checked_at.isoformat() if config.last_checked_at else None,
    }
