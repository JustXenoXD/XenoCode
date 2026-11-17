"""Bounded tool-calling loop for XenoCode agents."""

from typing import Callable

from xenocode.tools.registry import ToolRegistry


class ToolEngineError(RuntimeError):
    pass


class ToolCallingEngine:

    def __init__(
        self,
        agent,
        registry: ToolRegistry,
        max_rounds: int = 12,
        max_calls: int = 24,
        max_result_chars: int = 8000,
    ):
        if not 1 <= max_rounds <= 40:
            raise ValueError("Invalid tool round limit.")

        self.agent = agent
        self.registry = registry
        self.max_rounds = max_rounds
        self.max_calls = max_calls
        self.max_result_chars = max_result_chars

    def run(
        self,
        task: str,
        context: str,
        extra_context: str = "",
        approval: Callable | None = None,
    ) -> str:

        messages = [
            {
                "role": "system",
                "content": self.agent.system_prompt,
            },
            {
                "role": "user",
                "content": (
                    f"TASK:\n{task}\n\n"
                    f"PROJECT CONTEXT:\n{context}\n\n"
                    f"ADDITIONAL CONTEXT:\n{extra_context}"
                ),
            },
        ]

        total_calls = 0

        for round_number in range(self.max_rounds):

            response = self.agent.provider.chat(
                messages,
                tools=self.registry.definitions(),
                model=self.agent.model,
            )

            if not isinstance(response, dict):
                raise ToolEngineError(
                    "Provider returned an invalid response."
                )

            content = response.get("content", "")

            if not isinstance(content, str):
                content = ""

            tool_calls = response.get("tool_calls") or []

            if not isinstance(tool_calls, list):
                raise ToolEngineError(
                    "Provider returned invalid tool calls."
                )

            assistant_message = {
                "role": "assistant",
                "content": content,
            }

            if tool_calls:
                assistant_message["tool_calls"] = tool_calls

            messages.append(assistant_message)

            if not tool_calls:
                if not content.strip():
                    raise ToolEngineError(
                        "Model returned an empty final response."
                    )

                return content.strip()

            if total_calls + len(tool_calls) > self.max_calls:
                raise ToolEngineError(
                    "Maximum tool-call limit reached."
                )

            for call in tool_calls:

                function = (
                    call.get("function", {})
                    if isinstance(call, dict)
                    else {}
                )

                if not isinstance(function, dict):
                    function = {}

                name = function.get("name")
                arguments = function.get("arguments", {})

                if not isinstance(name, str):
                    name = "invalid_tool_call"

                try:
                    result = self.registry.execute(
                        name,
                        arguments,
                        approval=approval,
                    )

                except Exception as exc:
                    result = (
                        f"TOOL_ERROR: {type(exc).__name__}: {exc}"
                    )

                if len(result) > self.max_result_chars:
                    result = (
                        result[:self.max_result_chars]
                        + "\n[RESULT TRUNCATED]"
                    )

                messages.append({
                    "role": "tool",
                    "tool_name": name,
                    "content": result,
                })

                total_calls += 1

        raise ToolEngineError(
            f"Maximum tool rounds reached ({self.max_rounds})."
        )
