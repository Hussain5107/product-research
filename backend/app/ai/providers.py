from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.settings import get_settings


def _raise_safe_http_error(exc: httpx.HTTPStatusError, provider: str) -> None:
    status = exc.response.status_code
    reason = exc.response.reason_phrase
    raise RuntimeError(f"{provider} API request failed with HTTP {status} {reason}") from exc


class AIProvider(BaseModel, ABC):
    provider: str
    model: str
    configured: bool = False

    @abstractmethod
    def supports_reasoning(self) -> bool:
        ...

    @abstractmethod
    def client_kwargs(self) -> dict[str, Any]:
        ...

    @abstractmethod
    async def chat_completion(self, messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int = 2000) -> str:
        ...

    async def structured_completion(self, messages: list[dict[str, str]], schema: type[BaseModel], temperature: float = 0.2) -> BaseModel:
        response_text = await self.chat_completion(messages, temperature=temperature)
        try:
            payload = json.loads(response_text)
        except json.JSONDecodeError:
            payload = {"raw": response_text}
        return schema.model_validate(payload)


class OpenAIProvider(AIProvider):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    api_key: str = ""
    base_url: str = ""

    def supports_reasoning(self) -> bool:
        return True

    def client_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if self.api_key:
            kwargs["headers"] = {"Authorization": f"Bearer {self.api_key}"}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return kwargs

    async def chat_completion(self, messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int = 2000) -> str:
        async with httpx.AsyncClient(timeout=60.0, **self.client_kwargs()) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"},
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                _raise_safe_http_error(exc, "OpenAI")
            payload = response.json()
        choices = payload.get("choices", [])
        if not choices:
            raise RuntimeError("No choices returned from AI provider")
        message = choices[0].get("message", {})
        content = message.get("content", "")
        return content or ""


class AnthropicProvider(AIProvider):
    provider: str = "anthropic"
    model: str = "claude-3-5-haiku-20241022"
    api_key: str = ""

    supports_reasoning = lambda self: True  # type: ignore[assignment]

    def client_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if self.api_key:
            kwargs["headers"] = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01"}
        return kwargs

    async def chat_completion(self, messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int = 2000) -> str:
        # Anthropic uses a slightly different message model; convert from OpenAI-style for convenience.
        system = ""
        user_messages = []
        for message in messages:
            role = message.get("role", "user")
            if role == "system":
                system = message.get("content", "")
                continue
            user_messages.append({"role": "user" if role == "user" else "assistant", "content": message.get("content", "")})
        async with httpx.AsyncClient(timeout=60.0, **self.client_kwargs()) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "system": system,
                    "messages": user_messages,
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                _raise_safe_http_error(exc, "Anthropic")
            payload = response.json()
        content_block = payload.get("content", [])
        if not content_block:
            raise RuntimeError("No content returned from Anthropic")
        return content_block[0].get("text", "")


class GoogleProvider(AIProvider):
    provider: str = "google"
    model: str = "gemini-2.0-flash"
    api_key: str = ""
    base_url: str = ""

    supports_reasoning = lambda self: True  # type: ignore[assignment]

    def client_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        if self.api_key:
            kwargs["params"] = {"key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return kwargs

    async def chat_completion(self, messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int = 2000) -> str:
        async with httpx.AsyncClient(timeout=60.0, **self.client_kwargs()) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent".format(model=self.model),
                json={
                    "contents": [
                        {"role": "user", "parts": [{"text": message.get("content", "")}]}
                        for message in messages
                        if message.get("role") != "system"
                    ],
                    "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
                },
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                _raise_safe_http_error(exc, "Google")
            payload = response.json()
        candidates = payload.get("candidates", [])
        if not candidates:
            raise RuntimeError("No candidates returned from Google provider")
        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts:
            raise RuntimeError("No content parts returned from Google provider")
        return parts[0].get("text", "")


PROVIDER_CLASSES = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "google": GoogleProvider,
}


class AIORchestrator:
    def __init__(self, settings=None):
        self._provider: AIProvider | None = None
        self._settings = settings or get_settings()

    def _build_provider(self) -> AIProvider | None:
        provider_name = (self._settings.ai_provider or "").strip().lower()
        if not provider_name or not self._settings.effective_ai_api_key:
            return None
        provider_class = PROVIDER_CLASSES.get(provider_name)
        if not provider_class:
            return None
        instance = provider_class(
            provider=provider_name,
            model=self._settings.ai_model,
            api_key=self._settings.effective_ai_api_key,
            base_url=self._settings.ai_base_url,
        )
        instance.configured = bool(instance.api_key)
        return instance

    @property
    def provider(self) -> AIProvider | None:
        if self._provider is None:
            self._provider = self._build_provider()
        return self._provider

    @property
    def is_configured(self) -> bool:
        return bool(self.provider)

    async def chat_completion(self, messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int = 2000) -> str:
        if not self.provider:
            raise RuntimeError("AI provider not configured")
        return await self.provider.chat_completion(messages, temperature=temperature, max_tokens=max_tokens)

    async def structured_completion(self, messages: list[dict[str, str]], schema: type[BaseModel], temperature: float = 0.2) -> BaseModel:
        if not self.provider:
            raise RuntimeError("AI provider not configured")
        return await self.provider.structured_completion(messages, schema, temperature=temperature)

    def status(self) -> dict[str, Any]:
        return {
            "provider": self._settings.ai_provider,
            "model": self._settings.ai_model,
            "configured": self.is_configured,
            "message": self._status_message(),
        }

    def _status_message(self) -> str:
        if not self._settings.ai_provider:
            return "No AI provider selected. Choose a provider in Settings."
        if not self._settings.effective_ai_api_key:
            return "AI provider selected but API key is missing."
        if self._settings.ai_provider.strip().lower() not in PROVIDER_CLASSES:
            return "Selected AI provider is not supported."
        return "AI provider configured"
