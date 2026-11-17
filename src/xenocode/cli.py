"""XenoCode command-line interface."""

import argparse
import sys

from pathlib import Path

from xenocode import __version__
from xenocode.config import XenoConfig
from xenocode.providers.ollama import OllamaProvider
from xenocode.core.orchestrator import XenoOrchestrator
from xenocode.core.context import ProjectContextBuilder
from xenocode.core.swarm import AgentSwarm


def build_parser():

    parser = argparse.ArgumentParser(
        prog="xenocode",
        description="Local-first multi-agent coding AI.",
    )

    parser.add_argument("task", nargs="*")

    parser.add_argument("--workspace", default=".")

    parser.add_argument(
        "--host",
        default="http://127.0.0.1:11434",
    )

    parser.add_argument(
        "--model",
        default="qwen2.5-coder:7b",
    )

    parser.add_argument("--architect-model")
    parser.add_argument("--reviewer-model")

    parser.add_argument("--num-ctx", type=int, default=4096)
    parser.add_argument("--timeout", type=int, default=180)

    parser.add_argument("--plan-only", action="store_true")
    parser.add_argument("--no-review", action="store_true")
    parser.add_argument("--list-models", action="store_true")

    parser.add_argument(
        "--repairs",
        type=int,
        default=2,
    )

    parser.add_argument(
        "--swarm-agents",
        type=int,
        default=0,
        metavar="N",
        help="Launch a swarm with N agents (1-500).",
    )

    parser.add_argument(
        "--swarm-concurrency",
        type=int,
        default=1,
        help="Maximum simultaneous swarm requests (1-8).",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
    )

    return parser


def main(argv=None):

    parser = build_parser()
    args = parser.parse_args(argv)

    try:

        if args.swarm_agents < 0 or args.swarm_agents > 500:
            parser.error("--swarm-agents must be between 0 and 500.")

        config = XenoConfig(
            ollama_url=args.host,
            model=args.model,
            architect_model=args.architect_model,
            reviewer_model=args.reviewer_model,
            num_ctx=args.num_ctx,
            timeout=args.timeout,
            max_repair_attempts=args.repairs,
            swarm_concurrency=args.swarm_concurrency,
            workspace=Path(args.workspace),
        )

        provider = OllamaProvider(config)

        if args.list_models:

            models = provider.list_models()

            print(
                "\n".join(models)
                if models
                else "No models installed."
            )

            return 0

        task = " ".join(args.task).strip()

        if not task:
            parser.error("Provide a task or use --list-models.")

        if args.swarm_agents:

            context = ProjectContextBuilder(
                config.workspace,
            ).build()

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
                agent_count=args.swarm_agents,
            )

            print("\n" + result.report())

            return 0 if result.successful_agents else 1

        orchestrator = XenoOrchestrator(
            config,
            provider,
        )

        result = orchestrator.run(
            task,
            plan_only=args.plan_only,
            review=not args.no_review,
        )

        print("\n" + result.report())

        return 0

    except KeyboardInterrupt:

        print("\nStopped by user.", file=sys.stderr)
        return 130

    except Exception as exc:

        print(
            f"\nXenoCode error: {exc}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
