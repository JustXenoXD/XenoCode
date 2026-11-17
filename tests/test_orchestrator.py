import tempfile
import unittest

from pathlib import Path

from xenocode.config import XenoConfig
from xenocode.core.orchestrator import XenoOrchestrator
from xenocode.core.state import RunStatus


class FakeProvider:

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.requests = []

    def chat(self, messages, tools=None, *, model=None):
        self.calls.append(model)
        self.requests.append({
            "model": model,
            "messages": [dict(message) for message in messages],
            "tools": tools,
        })

        if not self.responses:
            raise RuntimeError("No fake responses available.")

        return {
            "role": "assistant",
            "content": self.responses.pop(0),
        }


class OrchestratorTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

        (self.root / "README.md").write_text(
            "# Test project",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_three_agent_workflow(self):

        provider = FakeProvider([
            "Architecture plan.",
            "Implementation proposal.",
            "VERDICT: PASS\nNo blocking issues.",
        ])

        config = XenoConfig(
            workspace=self.root,
        )

        agent = XenoOrchestrator(config, provider)

        result = agent.run("Improve this project.")

        self.assertEqual(
            result.status,
            RunStatus.COMPLETED,
        )

        self.assertEqual(len(result.stages), 3)

        self.assertIn("Architecture", result.plan)
        self.assertIn("VERDICT: PASS", result.review)

        for request in provider.requests:
            user_content = "\\n".join(
                str(message.get("content", ""))
                for message in request["messages"]
                if message.get("role") == "user"
            )
            self.assertIn("# Repository Map:", user_content)

        engineer_tools = provider.requests[1]["tools"]
        tool_names = [
            item["function"]["name"]
            for item in engineer_tools
        ]
        self.assertIn("get_repository_map", tool_names)

    def test_plan_only(self):

        provider = FakeProvider([
            "Plan only.",
        ])

        config = XenoConfig(
            workspace=self.root,
        )

        agent = XenoOrchestrator(config, provider)

        result = agent.run(
            "Analyze the project.",
            plan_only=True,
        )

        self.assertEqual(
            result.status,
            RunStatus.COMPLETED,
        )

        self.assertEqual(len(provider.calls), 1)

    def test_repair_workflow(self):

        provider = FakeProvider([
            "Initial plan.",
            "Initial implementation.",
            "VERDICT: NEEDS_CHANGES\nFix a missing edge case.",
            "Root cause: missing edge case.",
            "Revised implementation.",
            "VERDICT: PASS\nIssue addressed.",
        ])

        config = XenoConfig(
            workspace=self.root,
            max_repair_attempts=1,
        )

        agent = XenoOrchestrator(config, provider)

        result = agent.run("Fix this project.")

        self.assertEqual(result.repair_attempts, 1)
        self.assertIn("VERDICT: PASS", result.review)
        self.assertEqual(len(provider.calls), 6)

        # Architect, Engineer, Reviewer and Debugger
        # must all receive the shared repository map.
        for request in provider.requests:
            user_content = "\\n".join(
                str(message.get("content", ""))
                for message in request["messages"]
                if message.get("role") == "user"
            )
            self.assertIn("# Repository Map:", user_content)


if __name__ == "__main__":
    unittest.main()
