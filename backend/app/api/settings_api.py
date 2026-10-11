from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any

from app.settings import get_settings, Settings
from app.ai.providers import AIORchestrator

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    postgres_dsn: str
    redis_url: str
    app_env: str
    api_host: str
    api_port: int
    ai_provider: str
    ai_model: str
    ai_is_configured: bool
    ai_status_message: str
    http_timeout_seconds: int
    max_concurrent_research_requests: int
    research_job_timeout_seconds: int
    api_access_token_configured: bool


class AIProviderUpdate(BaseModel):
    provider: str = ""
    model: str = "gpt-4o-mini"
    api_key: str = ""
    base_url: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_ai_api_key: str = ""


class SettingsUpdate(BaseModel):
    app_env: str | None = None
    api_host: str | None = None
    api_port: int | None = None
    ai: AIProviderUpdate | None = None
    http_timeout_seconds: int | None = None
    max_concurrent_research_requests: int | None = None
    research_job_timeout_seconds: int | None = None
    api_access_token: str | None = None


def _provider_message(settings: Settings, provider: str) -> str:
    if not provider:
        return "No AI provider selected."
    if not settings.effective_ai_api_key:
        return "AI provider selected but API key is missing."
    if provider.strip().lower() not in {"openai", "anthropic", "google"}:
        return "Selected AI provider is not supported."
    return "AI provider configured"


@router.get("/app", response_model=SettingsResponse)
async def get_app_settings(settings: Settings = Depends(get_settings)) -> SettingsResponse:
    return SettingsResponse(
        postgres_dsn=settings.postgres_dsn,
        redis_url=settings.redis_url,
        app_env=settings.app_env,
        api_host=settings.api_host,
        api_port=settings.api_port,
        ai_provider=settings.ai_provider,
        ai_model=settings.ai_model,
        ai_is_configured=settings.ai_is_configured,
        ai_status_message=_provider_message(settings, settings.ai_provider),
        http_timeout_seconds=settings.default_request_timeout_seconds,
        max_concurrent_research_requests=settings.max_concurrent_requests,
        research_job_timeout_seconds=settings.research_job_timeout_seconds,
        api_access_token_configured=bool(settings.api_access_token),
    )


@router.put("/ai", response_model=dict[str, Any])
async def update_ai_settings(
    payload: AIProviderUpdate,
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    changes: dict[str, Any] = {}

    if payload.provider:
        settings.ai_provider = payload.provider
        changes["ai_provider"] = payload.provider
    if payload.model:
        settings.ai_model = payload.model
        changes["ai_model"] = payload.model
    if payload.base_url is not None:
        settings.ai_base_url = payload.base_url
        changes["ai_base_url"] = payload.base_url

    # Credential fields should be handled carefully in a real deployment.
    # For this personal application we allow updates through the settings API,
    # but they are still stored as environment/runtime config only.
    if payload.api_key is not None:
        settings.ai_api_key = payload.api_key
        changes["ai_api_key_set"] = True
    if payload.openai_api_key is not None:
        settings.openai_api_key = payload.openai_api_key
        changes["openai_api_key_set"] = True
    if payload.anthropic_api_key is not None:
        settings.anthropic_api_key = payload.anthropic_api_key
        changes["anthropic_api_key_set"] = True
    if payload.google_ai_api_key is not None:
        settings.google_ai_api_key = payload.google_ai_api_key
        changes["google_ai_api_key_set"] = True

    return {
        "updated": changes,
        "ai_provider": settings.ai_provider,
        "ai_model": settings.ai_model,
        "ai_is_configured": settings.ai_is_configured,
        "ai_status_message": _provider_message(settings, settings.ai_provider),
    }


@router.get("/ai/status", response_model=dict[str, Any])
async def ai_status(
    orchestrator: AIORchestrator = Depends(AIORchestrator),
) -> dict[str, Any]:
    return orchestrator.status()
