from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol

import httpx


class ModelClient(Protocol):
    async def complete(self, profile: str, messages: list[dict[str, str]], *, timeout: float | None = None) -> str:
        ...


@dataclass(frozen=True)
class ModelProfile:
    models: tuple[str, ...]
    timeout_seconds: float


DEFAULT_PROFILES = {
    "cheap_fast": ModelProfile(("sarvamai/sarvam-m",), 8.0),
    "careful": ModelProfile(("sarvamai/sarvam-m",), 20.0),
    "json_normalizer": ModelProfile(("sarvamai/sarvam-m",), 8.0),
    "summary": ModelProfile(("sarvamai/sarvam-m",), 20.0),
}


class OpenRouterModelClient:
    def __init__(
        self,
        api_key: str | None = None,
        profiles: dict[str, ModelProfile] | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.profiles = profiles or DEFAULT_PROFILES
        self.http_client = http_client or httpx.AsyncClient(base_url="https://openrouter.ai/api/v1")

    async def complete(self, profile: str, messages: list[dict[str, str]], *, timeout: float | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        model_profile = self.profiles[profile]
        last_error: Exception | None = None
        for model in model_profile.models:
            try:
                response = await self.http_client.post(
                    "/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": model, "messages": messages},
                    timeout=timeout or model_profile.timeout_seconds,
                )
                response.raise_for_status()
                payload: dict[str, Any] = response.json()
                return str(payload["choices"][0]["message"]["content"])
            except Exception as exc:
                last_error = exc
        raise RuntimeError(f"OpenRouter completion failed for profile {profile}") from last_error


class NullModelClient:
    async def complete(self, profile: str, messages: list[dict[str, str]], *, timeout: float | None = None) -> str:
        raise RuntimeError("No model client configured")
