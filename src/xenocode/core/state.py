"""Persistent-in-memory state for an XenoCode run."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


def now():
    return datetime.now(timezone.utc).isoformat()


class RunStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class StageRecord:
    role: str
    model: str
    output: str
    started_at: str
    finished_at: str
    success: bool = True


@dataclass
class RunState:
    task: str
    run_id: str = field(default_factory=lambda: uuid4().hex)
    status: RunStatus = RunStatus.CREATED
    created_at: str = field(default_factory=now)

    context: str = ""
    plan: str = ""
    implementation: str = ""
    review: str = ""

    repair_attempts: int = 0
    error: str | None = None

    stages: list[StageRecord] = field(default_factory=list)

    def add_stage(self, record: StageRecord):
        self.stages.append(record)

    def report(self) -> str:
        sections = [
            f"# XenoCode execution report",
            f"Run: {self.run_id}",
            f"Status: {self.status.value}",
            f"Task: {self.task}",
        ]

        for title, content in (
            ("Architect", self.plan),
            ("Engineer", self.implementation),
            ("Reviewer", self.review),
        ):
            if content:
                sections.extend([f"\n## {title}\n", content])

        if self.error:
            sections.extend(["\n## Error\n", self.error])

        sections.append(
            f"\nRepair attempts: {self.repair_attempts}"
        )

        return "\n".join(sections)
