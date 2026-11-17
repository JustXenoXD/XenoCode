"""Ollama API provider."""

import json

from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from xenocode.config import XenoConfig
from xenocode.providers.base import ProviderError


class OllamaProvider:

    def __init__(self, config: XenoConfig):
        self.config = config
        self.base_url = config.ollama_url.rstrip("/")

    def _request(
        self,
        endpoint: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        data = None

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")

        request = Request(
            self.base_url + endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="GET" if payload is None else "POST",
        )

        try:
            with urlopen(
                request,
                timeout=self.config.timeout,
            ) as response:

                result = json.loads(
                    response.read().decode("utf-8")
                )

        except HTTPError as exc:
            details = exc.read().decode(
                "utf-8",
                errors="replace",
            )

            raise ProviderError(
                f"Ollama HTTP {exc.code}: {details[:1000]}"
            ) from exc

        except (URLError, TimeoutError, OSError) as exc:
            raise ProviderError(
                f"Cannot connect to Ollama: {exc}"
            ) from exc

        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ProviderError(
                "Ollama returned invalid JSON."
            ) from exc

        if not isinstance(result, dict):
            raise ProviderError("Unexpected API response.")

        return result

    def list_models(self) -> list[str]:

        result = self._request("/api/tags")

        models = result.get("models", [])

        if not isinstance(models, list):
            raise ProviderError("Invalid model list.")

        return [
            item["name"]
            for item in models
            if isinstance(item, dict)
            and isinstance(item.get("name"), str)
        ]

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
    ) -> dict[str, Any]:

        payload = {
            "model": model or self.config.model,
            "messages": messages,
            "stream": False,
            "keep_alive": "5m",
            "options": {
                "temperature": self.config.temperature,
                "num_ctx": self.config.num_ctx,
            },
        }

        if tools:
            payload["tools"] = tools

        result = self._request(
            "/api/chat",
            payload,
        )

        message = result.get("message")

        if not isinstance(message, dict):
            raise ProviderError(
                "Missing assistant message."
            )

        return message
