from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    postgres_dsn: str = "sqlite+aiosqlite:///./producthunter.db"
    redis_url: str = "redis://localhost:6379/0"

    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    ai_provider: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_api_key: str = ""
    ai_base_url: str = ""

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_ai_api_key: str = ""
    cjdropshipping_api_key: str = ""
    zendrop_api_key: str = ""
    spocket_api_key: str = ""
    syncee_api_key: str = ""
    google_trends_api_key: str = ""

    default_request_timeout_seconds: int = 30
    max_concurrent_requests: int = 8
    research_job_timeout_seconds: int = 600

    api_access_token: str = ""

    @property
    def effective_ai_api_key(self) -> str:
        if self.ai_api_key:
            return self.ai_api_key
        provider = self.ai_provider.strip().lower()
        if provider == "openai":
            return self.openai_api_key
        if provider == "anthropic":
            return self.anthropic_api_key
        if provider == "google":
            return self.google_ai_api_key
        return ""

    @property
    def ai_is_configured(self) -> bool:
        return bool(self.ai_provider.strip() and self.effective_ai_api_key.strip())

    def ai_client_kwargs(self) -> dict:
        result: dict = {"model": self.ai_model}
        provider = self.ai_provider.strip().lower()
        if provider in {"openai", "azure"} or not provider:
            if self.ai_base_url.strip():
                result["base_url"] = self.ai_base_url.strip()
            return result
        if provider in {"anthropic"}:
            return result
        if provider in {"google"}:
            return result
        return result


@lru_cache
def get_settings() -> Settings:
    return Settings()
