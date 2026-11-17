# XenoCode Project State

Version: 0.1.0
Development status: Early prototype

## Environment

- Python 3.13.13 tested on Android/Termux.
- Editable package installation verified.
- CLI entry point verified.
- GitHub repository connected.
- GitHub Actions workflow created, remote execution not yet verified.

## Implemented components

- Central configuration.
- Ollama HTTP provider.
- Provider registry.
- Architect, Engineer, Reviewer and Debugger agents.
- Project context builder.
- Controlled filesystem operations.
- Workspace path validation.
- Secret-file and symlink protection.
- Text search.
- Test runner with approval protection.
- Tool registry and argument validation.
- Terminal approval mechanism.
- Bounded tool-calling engine.
- AST-based mathematical expression evaluator.
- CLI.
- Multi-agent orchestrator.

## Agent Swarm

Modules:

- core/decomposer.py
- core/agent_pool.py
- core/consensus.py
- core/swarm.py
- agents/swarm_worker.py

Features:

- Up to 500 logical agent assignments.
- Ten specialist categories.
- Multiple reasoning perspectives.
- Bounded concurrency.
- Hierarchical consensus.
- Unified engineering proposal.
- Failure tracking.
- Approval-protected swarm invocation.

The default concurrency is 1, configurable up to 8.

The swarm has been tested with a FakeProvider.
Real LLM execution has not yet been verified.

## Security

- Workspace path traversal protection.
- Absolute path rejection.
- Symbolic link rejection.
- Protected directory and secret-file filtering.
- Bounded file sizes.
- Explicit approval for write_file, run_tests and spawn_agent_swarm.
- Read-only and calculation tools do not require approval.

The separate security/permissions.py module is not implemented.

## Mathematical engine

- AST-based arithmetic evaluation.
- Addition, subtraction, multiplication and division.
- Integer division and modulo.
- Exponentiation with limits.
- Unary operators.
- Rejection of names, function calls and unsupported expressions.
- Expression complexity and result-size limits.

The calculate tool is registered in the default ToolRegistry.

## Verification

Latest local verification:

- 48 unit tests passed.
- Python compileall passed.
- pip install -e . passed.
- xenocode --version passed.
- xenocode --help passed.

Test environment: Python 3.13.13 on Termux.

## Known limitations

- Ollama was not reachable at 127.0.0.1:11434 during testing.
- Real LLM tool calling has not been tested.
- Swarm tests currently use a FakeProvider.
- All swarm workers use the configured model by default.
- Logical agent assignments are not 500 simultaneously running models.
- Persistent memory is not implemented.
- Workspace indexing and repository mapping are not implemented.
- Agent prompt files are incomplete.
- The separate permissions module is not implemented.
- GitHub Actions has not yet been verified through a remote workflow run.

## Next objectives

1. Implement workspace indexing and repository mapping.
2. Write and refine specialist agent prompts.
3. Implement persistent memory.
4. Verify Ollama integration with a real model.
5. Improve security regression tests.
6. Add coding benchmarks.
7. Consider multi-model routing.

## Workspace Intelligence Engine

Implemented:

- Bounded workspace indexing.
- File metadata and SHA-256 fingerprints.
- Language detection.
- Python import extraction.
- Python class and function extraction.
- Invalid Python syntax detection.
- File count and byte limits.
- Secret-file and symlink filtering through PathGuard.
- Repository tree generation.
- Bounded architecture map output.
- get_repository_map tool registration.

## Shared Agent Context

The orchestrator enriches the project context with a repository map.

Verified with FakeProvider:

- Architect receives the repository map.
- Engineer receives the repository map and tool definitions.
- Reviewer receives the repository map.
- Debugger receives the repository map during repair workflows.

## Latest Verification

- 62 unit tests passed.
- compileall passed.
- Editable package installation passed.
- CLI version and help passed.
- Workspace integration tests passed.
- Orchestrator context integration tests passed.

Real Ollama integration is still unverified.
GitHub Actions remote execution is still unverified.
The latest local changes have not yet been pushed to GitHub.
