import tempfile
import unittest

from pathlib import Path

from xenocode.tools.engine import ToolCallingEngine
from xenocode.memory.store import MemoryStore
from xenocode.tools.registry import build_default_registry


class FakeProvider:

    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def chat(self, messages, tools=None, *, model=None):

        self.requests.append({
            "messages": list(messages),
            "tools": tools,
            "model": model,
        })

        return self.responses.pop(0)


class FakeAgent:

    role = "Engineer"
    model = "fake-model"
    system_prompt = "You are a software engineer."

    def __init__(self, provider):
        self.provider = provider


class ToolEngineTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

        (self.root / "README.md").write_text(
            "# XenoCode\nA coding agent.",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_complete_tool_call_cycle(self):

        provider = FakeProvider([
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "read_file",
                            "arguments": {
                                "path": "README.md",
                            },
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "content": "I inspected the README successfully.",
            },
        ])

        agent = FakeAgent(provider)
        registry = build_default_registry(self.root)

        engine = ToolCallingEngine(
            agent,
            registry,
            max_rounds=4,
        )

        result = engine.run(
            "Inspect the README.",
            "Test project.",
        )

        self.assertIn("inspected", result)

        self.assertEqual(len(provider.requests), 2)

        second_messages = provider.requests[1]["messages"]

        tool_messages = [
            item for item in second_messages
            if item["role"] == "tool"
        ]

        self.assertEqual(len(tool_messages), 1)
        self.assertIn("XenoCode", tool_messages[0]["content"])

        available_tools = [
            item["function"]["name"]
            for item in provider.requests[0]["tools"]
        ]

        self.assertIn("read_file", available_tools)
        self.assertIn("write_file", available_tools)

    def test_empty_final_response_rejected(self):

        provider = FakeProvider([
            {
                "role": "assistant",
                "content": "",
            }
        ])

        engine = ToolCallingEngine(
            FakeAgent(provider),
            build_default_registry(self.root),
        )

        with self.assertRaises(Exception):
            engine.run("Test", "Context.")


    def test_calculator_tool_call_cycle(self):
        provider = FakeProvider([
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "calculate",
                            "arguments": {
                                "expression": "125 * 48",
                            },
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "content": "125 * 48 = 6000.",
            },
        ])

        registry = build_default_registry(self.root)
        engine = ToolCallingEngine(
            FakeAgent(provider),
            registry,
            max_rounds=4,
        )

        result = engine.run(
            "Calculate 125 multiplied by 48.",
            "Test project.",
        )

        self.assertIn("6000", result)
        self.assertEqual(len(provider.requests), 2)

        available_tools = [
            item["function"]["name"]
            for item in provider.requests[0]["tools"]
        ]
        self.assertIn("calculate", available_tools)

        tool_messages = [
            item
            for item in provider.requests[1]["messages"]
            if item["role"] == "tool"
            and item.get("tool_name") == "calculate"
        ]

        self.assertEqual(len(tool_messages), 1)
        self.assertEqual(tool_messages[0]["content"], "6000")


    def test_memory_tool_call_cycle(self):
        provider = FakeProvider([
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "remember_memory",
                            "arguments": {
                                "category": "decision",
                                "content": "Keep providers separate from orchestration.",
                                "tags": ["architecture"],
                            },
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "content": "The architecture decision was saved.",
            },
        ])

        store = MemoryStore(self.root)
        registry = build_default_registry(
            self.root,
            memory_store=store,
        )

        engine = ToolCallingEngine(
            FakeAgent(provider),
            registry,
            max_rounds=4,
        )

        result = engine.run(
            "Save the verified architecture decision.",
            "Test project.",
            approval=lambda name, args: True,
        )

        self.assertIn("saved", result.lower())
        self.assertEqual(len(store.recent()), 1)

        tool_messages = [
            item
            for item in provider.requests[1]["messages"]
            if item["role"] == "tool"
            and item.get("tool_name") == "remember_memory"
        ]

        self.assertEqual(len(tool_messages), 1)
        self.assertIn("saved successfully", tool_messages[0]["content"].lower())


if __name__ == "__main__":
    unittest.main()
