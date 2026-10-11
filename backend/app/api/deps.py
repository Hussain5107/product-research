from __future__ import annotations

from typing import AsyncGenerator, Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import yield_db_session
from app.settings import get_settings
from app.ai.providers import AIORchestrator
from app.connectors.registry import ConnectorRegistry, default_registry


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in yield_db_session():
        yield session


def get_settings_dep() -> get_settings.__class__:
    return get_settings()


def get_ai_orchestrator() -> AIORchestrator:
    return AIORchestrator(get_settings())


def get_registry() -> ConnectorRegistry:
    return default_registry()


async def require_access_token(request: Request) -> None:
    token = get_settings().api_access_token
    if not token:
        return
    provided = request.headers.get("x-api-token") or request.headers.get("x-access-token") or ""
    if provided != token:
        raise HTTPException(status_code=401, detail="Invalid access token")
