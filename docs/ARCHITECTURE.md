# XenoCode Architecture

## Core

The core package coordinates execution and project context.

## Standard Agents

- Architect: system design.
- Engineer: implementation.
- Reviewer: independent review.
- Debugger: fault analysis.

## Agent Swarm

The swarm system contains:

- TaskDecomposer
- SwarmWorker
- AgentPool
- ConsensusEngine
- AgentSwarm

### Execution pipeline

1. Validate requested agent count.
2. Generate diverse assignments.
3. Execute independent workers.
4. Collect successful and failed opinions.
5. Group successful opinions into batches.
6. Summarize each batch.
7. Produce one unified engineering proposal.

### Limits

- Maximum logical agents: 500.
- Default concurrency: 1.
- Maximum concurrency: 8.
- Default consensus batch size: 20.

### Important distinction

Logical agent count is not the number of simultaneously loaded models.

Workers use the configured provider and model.
Multiple workers may therefore make independent requests
to the same underlying model.

## Consensus principles

- Repetition is not proof.
- Minority opinions must be preserved when technically valid.
- Contradictions must be identified.
- Unsupported claims must be rejected.
- Final designs must explain trade-offs.

## File modification

Only the Engineer uses write_file.

File modifications require user approval.

Swarm workers are analysis-only.
