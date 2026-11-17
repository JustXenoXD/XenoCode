"""Coordinates XenoCode specialist agents and agent swarms."""

from datetime import datetime, timezone

from xenocode.agents.architect import ArchitectAgent
from xenocode.agents.engineer import EngineerAgent
from xenocode.agents.reviewer import ReviewerAgent
from xenocode.agents.debugger import DebuggerAgent

from xenocode.core.context import ProjectContextBuilder
from xenocode.core.state import (
    RunState,
    RunStatus,
    StageRecord,
)
from xenocode.core.swarm import AgentSwarm

from xenocode.tools.engine import ToolCallingEngine
from xenocode.tools.registry import build_default_registry
from xenocode.security.approvals import TerminalApproval
from xenocode.workspace.indexer import WorkspaceIndexer
from xenocode.workspace.repo_map import RepositoryMapBuilder


class OrchestratorError(RuntimeError):
    pass


class XenoOrchestrator:

    def __init__(
        self,
        config,
        provider,
        tool_registry=None,
        approval_callback=None,
    ):

        self.config = config
        self.provider = provider

        self.context_builder = ProjectContextBuilder(
            config.workspace,
        )

        self.approval_callback = (
            approval_callback
            if approval_callback is not None
            else TerminalApproval()
        )

        def run_swarm_tool(task, agent_count=5):

            if not 1 <= agent_count <= config.max_swarm_agents:
                raise ValueError(
                    f"Agent count must be between 1 "
                    f"and {config.max_swarm_agents}."
                )

            context = self._build_project_context()

            swarm = AgentSwarm(
                provider=provider,
                model=config.model,
                concurrency=config.swarm_concurrency,
                consensus_batch_size=config.swarm_consensus_batch_size,
                context_limit=config.swarm_context_chars,
            )

            result = swarm.run(
                task=task,
                context=context,
                agent_count=agent_count,
            )

            return result.report()

        self.tool_registry = (
            tool_registry
            if tool_registry is not None
            else build_default_registry(
                config.workspace,
                swarm_runner=run_swarm_tool,
            )
        )

        self.architect = ArchitectAgent(
            provider,
            config.planner,
            config.max_tool_rounds,
        )

        self.engineer = EngineerAgent(
            provider,
            config.model,
            config.max_tool_rounds,
        )

        self.reviewer = ReviewerAgent(
            provider,
            config.reviewer,
            config.max_tool_rounds,
        )

        self.debugger = DebuggerAgent(
            provider,
            config.model,
            config.max_tool_rounds,
        )

    def _execute(
        self,
        agent,
        state,
        task,
        context,
        extra="",
        with_tools=False,
    ):

        started = datetime.now(timezone.utc).isoformat()

        try:

            if with_tools:

                engine = ToolCallingEngine(
                    agent,
                    self.tool_registry,
                    max_rounds=self.config.max_tool_rounds,
                )

                result = engine.run(
                    task,
                    context,
                    extra,
                    approval=self.approval_callback,
                )

            else:

                result = agent.run(
                    task,
                    context,
                    extra,
                )

            finished = datetime.now(timezone.utc).isoformat()

            state.add_stage(
                StageRecord(
                    role=agent.role,
                    model=agent.model,
                    output=result,
                    started_at=started,
                    finished_at=finished,
                )
            )

            return result

        except Exception as exc:

            finished = datetime.now(timezone.utc).isoformat()

            state.add_stage(
                StageRecord(
                    role=agent.role,
                    model=agent.model,
                    output=str(exc),
                    started_at=started,
                    finished_at=finished,
                    success=False,
                )
            )

            raise OrchestratorError(
                f"{agent.role} failed: {exc}"
            ) from exc

    def _build_project_context(self) -> str:
        """Build shared context enriched with a repository map."""

        context = self.context_builder.build()

        index = WorkspaceIndexer(
            self.config.workspace,
        ).build()

        repository_map = RepositoryMapBuilder(
            max_output_chars=8000,
            max_symbols=100,
        ).build(index)

        return (
            context
            + "\n\n"
            + "PROJECT ARCHITECTURE MAP:\n"
            + repository_map
        )

    def run(
        self,
        task: str,
        plan_only: bool = False,
        review: bool = True,
    ) -> RunState:

        task = task.strip()

        if not task:
            raise ValueError("Task cannot be empty.")

        state = RunState(task=task)
        state.status = RunStatus.RUNNING

        try:

            print("\n[XenoCode] Building project context...")

            context = self._build_project_context()
            state.context = context

            print("[XenoCode] Starting Architect...")

            state.plan = self._execute(
                self.architect,
                state,
                task,
                context,
            )

            if plan_only:
                state.status = RunStatus.COMPLETED
                return state

            print("\n[XenoCode] Starting Engineer...")

            state.implementation = self._execute(
                self.engineer,
                state,
                task,
                context,
                "ARCHITECT PLAN:\n" + state.plan,
                with_tools=True,
            )

            if review:

                for attempt in range(
                    self.config.max_repair_attempts + 1
                ):

                    print("\n[XenoCode] Starting Reviewer...")

                    review_context = (
                        "ARCHITECT PLAN:\n"
                        + state.plan
                        + "\n\nENGINEER IMPLEMENTATION:\n"
                        + state.implementation
                    )

                    state.review = self._execute(
                        self.reviewer,
                        state,
                        task,
                        context,
                        review_context,
                    )

                    if "VERDICT: NEEDS_CHANGES" not in state.review:
                        break

                    if attempt >= self.config.max_repair_attempts:
                        break

                    state.repair_attempts += 1

                    print("\n[XenoCode] Starting Debugger...")

                    diagnosis = self._execute(
                        self.debugger,
                        state,
                        task,
                        context,
                        review_context
                        + "\n\nREVIEW FINDINGS:\n"
                        + state.review,
                    )

                    state.implementation = self._execute(
                        self.engineer,
                        state,
                        task,
                        context,
                        "PREVIOUS IMPLEMENTATION:\n"
                        + state.implementation
                        + "\n\nDEBUGGER DIAGNOSIS:\n"
                        + diagnosis,
                        with_tools=True,
                    )

            state.status = RunStatus.COMPLETED

        except Exception as exc:

            state.status = RunStatus.FAILED
            state.error = str(exc)
            raise

        return state
