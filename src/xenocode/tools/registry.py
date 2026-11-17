"""Tool registration, schema validation and execution."""

import re

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Callable

from xenocode.security.path_guard import PathGuard
from xenocode.tools.filesystem import FileSystemTools
from xenocode.tools.math_engine import MathEngine
from xenocode.tools.search import SearchTools
from xenocode.tools.test_runner import TestRunner
from xenocode.workspace.indexer import WorkspaceIndexer
from xenocode.workspace.repo_map import RepositoryMapBuilder


class ToolError(RuntimeError):
    pass


class ApprovalDenied(ToolError):
    pass


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    handler: Callable
    requires_approval: bool = False


class ToolRegistry:

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        handler: Callable,
        requires_approval: bool = False,
    ) -> None:

        if not re.fullmatch(r"[a-z][a-z0-9_]{1,63}", name):
            raise ValueError("Invalid tool name.")

        if name in self._tools:
            raise ValueError(f"Tool already registered: {name}")

        if not isinstance(parameters, dict):
            raise ValueError("Tool parameters must be a dictionary.")

        if parameters.get("type") != "object":
            raise ValueError("Tool schema must describe an object.")

        self._tools[name] = Tool(
            name=name,
            description=description,
            parameters=deepcopy(parameters),
            handler=handler,
            requires_approval=requires_approval,
        )

    def definitions(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": deepcopy(tool.parameters),
                },
            }
            for tool in self._tools.values()
        ]

    @staticmethod
    def _matches_type(value: Any, expected: str) -> bool:

        if expected == "string":
            return isinstance(value, str)

        if expected == "integer":
            return type(value) is int

        if expected == "number":
            return type(value) in (int, float)

        if expected == "boolean":
            return type(value) is bool

        if expected == "object":
            return isinstance(value, dict)

        if expected == "array":
            return isinstance(value, list)

        return False

    def _validate(self, tool: Tool, arguments: dict) -> None:

        if not isinstance(arguments, dict):
            raise ToolError("Tool arguments must be an object.")

        schema = tool.parameters
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        missing = set(required) - set(arguments)

        if missing:
            raise ToolError(
                f"Missing required arguments: {sorted(missing)}"
            )

        unknown = set(arguments) - set(properties)

        if unknown and schema.get("additionalProperties", False) is False:
            raise ToolError(
                f"Unknown arguments: {sorted(unknown)}"
            )

        for key, value in arguments.items():

            expected = properties[key].get("type")

            if not self._matches_type(value, expected):
                raise ToolError(
                    f"Invalid type for argument: {key}"
                )

    def execute(
        self,
        name: str,
        arguments: dict,
        approval: Callable | None = None,
    ) -> str:

        tool = self._tools.get(name)

        if tool is None:
            raise ToolError(f"Unknown tool: {name}")

        self._validate(tool, arguments)

        if tool.requires_approval:
            if approval is None or not approval(name, arguments):
                raise ApprovalDenied(
                    f"User approval required for {name}."
                )

        result = tool.handler(**arguments)

        return result if isinstance(result, str) else str(result)


def build_default_registry(
    workspace,
    swarm_runner: Callable | None = None,
) -> ToolRegistry:

    guard = PathGuard(workspace)

    filesystem = FileSystemTools(guard)
    search = SearchTools(guard)
    tests = TestRunner(guard)

    registry = ToolRegistry()

    def get_repository_map():
        index = WorkspaceIndexer(workspace).build()
        return RepositoryMapBuilder().build(index)

    registry.register(
        "get_repository_map",
        (
            "Build a bounded map of the repository structure, "
            "programming languages, Python imports and symbols."
        ),
        {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        get_repository_map,
    )


    math_engine = MathEngine()

    registry.register(
        "calculate",
        "Safely evaluate a mathematical expression.",
        {
            "type": "object",
            "properties": {
                "expression": {"type": "string"},
            },
            "required": ["expression"],
            "additionalProperties": False,
        },
        math_engine.calculate,
    )


    registry.register(
        "read_file",
        "Read a UTF-8 source or documentation file.",
        {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        filesystem.read_file,
    )

    registry.register(
        "list_files",
        "List readable files in a project directory.",
        {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
            },
            "additionalProperties": False,
        },
        filesystem.list_files,
    )

    registry.register(
        "search_text",
        "Search for text across project files.",
        {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "path": {"type": "string"},
                "max_results": {"type": "integer"},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        search.search_text,
    )

    registry.register(
        "write_file",
        "Create or modify a project text file. Requires user approval.",
        {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"},
                "overwrite": {"type": "boolean"},
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
        filesystem.write_file,
        requires_approval=True,
    )

    registry.register(
        "run_tests",
        "Run the project's Python unittest suite. Requires user approval.",
        {
            "type": "object",
            "properties": {
                "timeout": {"type": "integer"},
            },
            "additionalProperties": False,
        },
        tests.run_tests,
        requires_approval=True,
    )

    if swarm_runner is not None:

        registry.register(
            "spawn_agent_swarm",
            (
                "Launch independent AI specialists to analyze an engineering "
                "problem, compare different approaches and produce one "
                "unified technical proposal. Expensive operation: requires "
                "explicit user approval."
            ),
            {
                "type": "object",
                "properties": {
                    "task": {"type": "string"},
                    "agent_count": {"type": "integer"},
                },
                "required": ["task"],
                "additionalProperties": False,
            },
            swarm_runner,
            requires_approval=True,
        )

    return registry
