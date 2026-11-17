"""Base interface for AI providers."""

from typing import Any, Protocol


class ProviderError(RuntimeError):
    """AI provider communication or response error."""


class ModelProvider(Protocol):

    def list_models(self) -> list[str]:
        ...

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
    ) -> dict[str, Any]:
        ...
