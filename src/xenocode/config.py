"""Central configuration for XenoCode."""

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class XenoConfig:

    provider: str = "ollama"
    ollama_url: str = "http://127.0.0.1:11434"

    model: str = "qwen2.5-coder:7b"
    architect_model: str | None = None
    reviewer_model: str | None = None

    temperature: float = 0.2
    num_ctx: int = 4096
    timeout: int = 180

    max_tool_rounds: int = 12
    max_repair_attempts: int = 2

    max_swarm_agents: int = 500
    swarm_concurrency: int = 1
    swarm_consensus_batch_size: int = 20
    swarm_context_chars: int = 12000

    workspace: Path = Path(".")

    def __post_init__(self):

        if self.provider != "ollama":
            raise ValueError("Unsupported provider.")

        parsed = urlsplit(self.ollama_url)

        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Invalid Ollama URL.")

        if not 0 <= self.temperature <= 2:
            raise ValueError("Temperature must be between 0 and 2.")

        if self.num_ctx < 512:
            raise ValueError("Context must be at least 512 tokens.")

        if self.timeout < 5:
            raise ValueError("Timeout must be at least 5 seconds.")

        if not 1 <= self.max_tool_rounds <= 40:
            raise ValueError("Invalid tool round limit.")

        if not 0 <= self.max_repair_attempts <= 3:
            raise ValueError("Invalid repair attempt limit.")

        if not self.model.strip():
            raise ValueError("A model must be specified.")

        if not 1 <= self.max_swarm_agents <= 500:
            raise ValueError("Maximum swarm agents must be 1-500.")

        if not 1 <= self.swarm_concurrency <= 8:
            raise ValueError("Swarm concurrency must be 1-8.")

        if not 2 <= self.swarm_consensus_batch_size <= 40:
            raise ValueError("Invalid swarm consensus batch size.")

        if not 1000 <= self.swarm_context_chars <= 50000:
            raise ValueError("Invalid swarm context limit.")

    @property
    def planner(self) -> str:
        return self.architect_model or self.model

    @property
    def reviewer(self) -> str:
        return self.reviewer_model or self.model
