"""Common interface for all XenoCode agents."""

from abc import ABC, abstractmethod
from typing import Any


class AgentError(RuntimeError):
    pass


class BaseAgent(ABC):

    def __init__(
        self,
        provider,
        model: str,
        max_rounds: int = 12,
    ):
        self.provider = provider
        self.model = model
        self.max_rounds = max_rounds

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        pass

    @property
    @abstractmethod
    def role(self) -> str:
        pass

    def run(
        self,
        task: str,
        context: str,
        extra_context: str = "",
    ) -> str:

        user_message = (
            f"USER TASK:\n{task}\n\n"
            f"PROJECT CONTEXT:\n{context}\n\n"
            f"ADDITIONAL INFORMATION:\n{extra_context}"
        )

        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        response = self.provider.chat(
            messages,
            model=self.model,
        )

        content = response.get("content")

        if not isinstance(content, str) or not content.strip():
            raise AgentError(
                f"{self.role} returned an empty response."
            )

        return content.strip()
