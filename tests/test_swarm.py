import tempfile
import unittest

from pathlib import Path

from xenocode.config import XenoConfig
from xenocode.core.decomposer import TaskDecomposer
from xenocode.core.agent_pool import AgentPool
from xenocode.core.swarm import AgentSwarm
from xenocode.tools.registry import (
    ApprovalDenied,
    build_default_registry,
)


class FakeProvider:

    def __init__(self):
        self.calls = []

    def chat(self, messages, tools=None, *, model=None):

        system = messages[0]["content"].upper()

        self.calls.append(messages)

        if "CONSENSUS ANALYST" in system:
            content = "Batch synthesis: independent technical findings."

        elif "MASTER ENGINEER" in system:
            content = "FINAL DESIGN: Unified and reviewed proposal."

        else:
            content = """
PROPOSAL:
A modular architecture.

RATIONALE:
Separation of responsibilities.

ADVANTAGES:
Maintainability and extensibility.

TRADE_OFFS:
Additional complexity.

RISKS:
Integration issues.

RECOMMENDATIONS:
Use automated testing.
"""

        return {
            "role": "assistant",
            "content": content,
        }


class SwarmTests(unittest.TestCase):

    def test_assignment_generation(self):

        assignments = TaskDecomposer.create_assignments(100)

        self.assertEqual(len(assignments), 100)

        self.assertEqual(
            assignments[0].agent_id,
            "XENO-001",
        )

        self.assertEqual(
            assignments[-1].agent_id,
            "XENO-100",
        )

    def test_maximum_500_agents(self):

        assignments = TaskDecomposer.create_assignments(500)

        self.assertEqual(len(assignments), 500)

        perspectives = {
            (item.specialty, item.perspective)
            for item in assignments
        }

        self.assertEqual(len(perspectives), 500)

        self.assertEqual(
            len({item.agent_id for item in assignments}),
            500,
        )

    def test_agent_limit_rejected(self):

        with self.assertRaises(ValueError):
            TaskDecomposer.create_assignments(501)

    def test_invalid_agent_count(self):

        with self.assertRaises(ValueError):
            TaskDecomposer.create_assignments(0)

        with self.assertRaises(ValueError):
            TaskDecomposer.create_assignments(True)

    def test_invalid_pool_concurrency(self):

        with self.assertRaises(ValueError):
            AgentPool(max_workers=0)

        with self.assertRaises(ValueError):
            AgentPool(max_workers=9)

    def test_swarm_execution(self):

        provider = FakeProvider()

        swarm = AgentSwarm(
            provider=provider,
            model="fake-model",
            concurrency=2,
            consensus_batch_size=2,
        )

        result = swarm.run(
            task="Design a high-performance database.",
            context="Python software project.",
            agent_count=5,
        )

        self.assertEqual(result.requested_agents, 5)
        self.assertEqual(result.successful_agents, 5)
        self.assertEqual(result.failed_agents, 0)

        self.assertIn("FINAL DESIGN", result.synthesis)

        self.assertIn(
            "Unified Engineering Proposal",
            result.report(),
        )

        self.assertGreater(len(provider.calls), 5)

    def test_swarm_with_worker_failures(self):

        class FailingProvider:

            def chat(self, messages, tools=None, *, model=None):
                raise RuntimeError("Simulated connection failure.")

        swarm = AgentSwarm(
            provider=FailingProvider(),
            model="fake-model",
            concurrency=2,
        )

        with self.assertRaises(RuntimeError):
            swarm.run(
                task="Test failure handling.",
                context="Test context.",
                agent_count=3,
            )

    def test_swarm_config(self):

        config = XenoConfig()

        self.assertEqual(config.max_swarm_agents, 500)
        self.assertEqual(config.swarm_concurrency, 1)
        self.assertEqual(config.swarm_consensus_batch_size, 20)

    def test_invalid_swarm_config(self):

        with self.assertRaises(ValueError):
            XenoConfig(max_swarm_agents=501)

        with self.assertRaises(ValueError):
            XenoConfig(swarm_concurrency=9)

        with self.assertRaises(ValueError):
            XenoConfig(swarm_consensus_batch_size=1)

    def test_swarm_tool_requires_approval(self):

        with tempfile.TemporaryDirectory() as directory:

            registry = build_default_registry(
                directory,
                swarm_runner=lambda task, agent_count=5:
                    f"Executed swarm with {agent_count} agents.",
            )

            with self.assertRaises(ApprovalDenied):

                registry.execute(
                    "spawn_agent_swarm",
                    {
                        "task": "Analyze architecture.",
                        "agent_count": 10,
                    },
                )

            result = registry.execute(
                "spawn_agent_swarm",
                {
                    "task": "Analyze architecture.",
                    "agent_count": 10,
                },
                approval=lambda name, args: True,
            )

            self.assertIn("10 agents", result)


if __name__ == "__main__":
    unittest.main()
