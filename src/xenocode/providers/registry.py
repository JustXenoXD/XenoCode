"""AI provider registration and selection."""

from collections.abc import Callable

from xenocode.config import XenoConfig
from xenocode.providers.base import ModelProvider, ProviderError
from xenocode.providers.ollama import OllamaProvider


ProviderFactory = Callable[[XenoConfig], ModelProvider]


class ProviderRegistry:

    def __init__(self):
        self._factories: dict[str, ProviderFactory] = {}

        self.register(
            "ollama",
            OllamaProvider,
        )

    def register(
        self,
        name: str,
        factory: ProviderFactory,
    ) -> None:

        key = name.strip().lower()

        if not key:
            raise ValueError("Provider name cannot be empty.")

        if key in self._factories:
            raise ValueError(f"Provider already registered: {key}")

        self._factories[key] = factory

    def create(
        self,
        config: XenoConfig,
    ) -> ModelProvider:

        factory = self._factories.get(config.provider)

        if factory is None:
            raise ProviderError(
                f"Unknown provider: {config.provider}"
            )

        return factory(config)

    def available(self) -> list[str]:
        return sorted(self._factories)
