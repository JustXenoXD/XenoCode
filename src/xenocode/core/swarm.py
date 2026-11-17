"""Main coordinator for the XenoCode multi-agent swarm."""

from dataclasses import dataclass

from xenocode.agents.swarm_worker import SwarmWorker, AgentOpinion
from xenocode.core.decomposer import TaskDecomposer
from xenocode.core.agent_pool import AgentPool
from xenocode.core.consensus import ConsensusEngine


@dataclass
class SwarmResult:
    task: str
    requested_agents: int
    opinions: list[AgentOpinion]
    synthesis: str

    @property
    def successful_agents(self):
        return sum(item.success for item in self.opinions)

    @property
    def failed_agents(self):
        return len(self.opinions) - self.successful_agents

    def report(self) -> str:

        lines = [
            "# XenoCode Agent Swarm Report",
            "",
            f"Requested agents: {self.requested_agents}",
            f"Completed successfully: {self.successful_agents}",
            f"Failed: {self.failed_agents}",
            "",
            "## Specialist Distribution",
            "",
        ]

        specialties = {}

        for opinion in self.opinions:
            key = opinion.specialty
            specialties[key] = specialties.get(key, 0) + 1

        for specialty, count in sorted(specialties.items()):
            lines.append(f"- {specialty}: {count}")

        lines.extend([
            "",
            "## Execution Failures",
            "",
        ])

        failures = [
            item for item in self.opinions
            if not item.success
        ]

        if failures:
            for item in failures:
                lines.append(
                    f"- {item.agent_id}: {item.error}"
                )
        else:
            lines.append("No worker failures.")

        lines.extend([
            "",
            "## Unified Engineering Proposal",
            "",
            self.synthesis,
        ])

        return "\n".join(lines)


class AgentSwarm:

    MAX_AGENTS = 500

    def __init__(
        self,
        provider,
        model: str,
        concurrency: int = 1,
        consensus_batch_size: int = 20,
        context_limit: int = 12000,
    ):

        if not 1000 <= context_limit <= 50000:
            raise ValueError("Invalid swarm context limit.")

        self.worker = SwarmWorker(provider, model)

        self.pool = AgentPool(
            max_workers=concurrency,
        )

        self.consensus = ConsensusEngine(
            provider,
            model,
            batch_size=consensus_batch_size,
        )

        self.context_limit = context_limit

    def run(
        self,
        task: str,
        context: str,
        agent_count: int = 5,
    ) -> SwarmResult:

        if not isinstance(task, str) or not task.strip():
            raise ValueError("Task cannot be empty.")

        assignments = TaskDecomposer.create_assignments(
            agent_count,
        )

        bounded_context = context[:self.context_limit]

        print(
            f"\n[Xeno Swarm] Launching {agent_count} logical agents."
        )

        print(
            f"[Xeno Swarm] Maximum concurrent requests: "
            f"{self.pool.max_workers}"
        )

        opinions = self.pool.execute(
            self.worker,
            assignments,
            task.strip(),
            bounded_context,
        )

        successful = sum(
            opinion.success for opinion in opinions
        )

        print(
            f"[Xeno Swarm] Completed: {successful}/{agent_count}"
        )

        if not successful:
            raise RuntimeError(
                "Every swarm worker failed. Check provider connectivity."
            )

        print("[Xeno Swarm] Building hierarchical consensus...")

        synthesis = self.consensus.synthesize(opinions)

        print("[Xeno Swarm] Final synthesis completed.")

        return SwarmResult(
            task=task,
            requested_agents=agent_count,
            opinions=opinions,
            synthesis=synthesis,
        )
