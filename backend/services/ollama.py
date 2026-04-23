"""Async Ollama client with primary/fallback model and streaming support."""

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)


# ─── Exceptions ───────────────────────────────────────────────────────────────


class OllamaError(Exception):
    pass


class OllamaConnectionError(OllamaError):
    pass


class OllamaModelNotFoundError(OllamaError):
    pass


class OllamaTimeoutError(OllamaError):
    pass


# ─── Client ───────────────────────────────────────────────────────────────────


class OllamaClient:
    def __init__(self) -> None:
        self._base = settings.ollama_base_url.rstrip("/")
        self._primary = settings.ollama_primary_model
        self._fallback = settings.ollama_fallback_model
        self._timeout = settings.ollama_timeout_seconds

    async def generate(self, prompt: str, system: str = "") -> str:
        """Generate text, trying the primary model then falling back on failure."""
        for model in (self._primary, self._fallback):
            try:
                return await self._generate_with(model, prompt, system)
            except (OllamaModelNotFoundError, OllamaTimeoutError) as exc:
                if model == self._fallback:
                    raise
                logger.warning("Primary model %s failed (%s), trying fallback", model, exc)
        raise OllamaError("Unreachable")

    async def stream(self, prompt: str, system: str = "") -> AsyncGenerator[str, None]:
        """Yield tokens from the primary model as they arrive."""
        async for token in self._stream_with(self._primary, prompt, system):
            yield token

    async def health(self) -> dict[str, Any]:
        """Return server reachability and per-model availability."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self._base}/api/tags")
                resp.raise_for_status()
                available = [m["name"] for m in resp.json().get("models", [])]
                return {
                    "status": "ok",
                    "primary_model": self._primary,
                    "primary_available": self._primary in available,
                    "fallback_model": self._fallback,
                    "fallback_available": self._fallback in available,
                    "available_models": available,
                }
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(f"Cannot reach Ollama at {self._base}") from exc
        except httpx.HTTPStatusError as exc:
            raise OllamaError(f"Ollama returned HTTP {exc.response.status_code}") from exc

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _generate_with(self, model: str, prompt: str, system: str) -> str:
        payload: dict[str, Any] = {"model": model, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(f"{self._base}/api/generate", json=payload)
                if resp.status_code == 404:
                    raise OllamaModelNotFoundError(f"Model not found: {model}")
                resp.raise_for_status()
                return str(resp.json()["response"])
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError(f"Request timed out for model {model}") from exc
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(f"Cannot reach Ollama at {self._base}") from exc

    async def _stream_with(self, model: str, prompt: str, system: str) -> AsyncGenerator[str, None]:
        payload: dict[str, Any] = {"model": model, "prompt": prompt, "stream": True}
        if system:
            payload["system"] = system
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                async with client.stream("POST", f"{self._base}/api/generate", json=payload) as resp:
                    if resp.status_code == 404:
                        raise OllamaModelNotFoundError(f"Model not found: {model}")
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        data = json.loads(line)
                        if token := data.get("response"):
                            yield token
                        if data.get("done"):
                            break
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError(f"Stream timed out for model {model}") from exc
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(f"Cannot reach Ollama at {self._base}") from exc


# Module-level singleton used by route handlers.
ollama = OllamaClient()
