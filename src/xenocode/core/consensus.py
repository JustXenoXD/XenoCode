"""Hierarchical synthesis of independent agent opinions."""

from xenocode.agents.swarm_worker import AgentOpinion


class ConsensusEngine:

    def __init__(
        self,
        provider,
        model: str,
        batch_size: int = 20,
        opinion_limit: int = 1200,
    ):

        if not 2 <= batch_size <= 40:
            raise ValueError("Invalid consensus batch size.")

        self.provider = provider
        self.model = model
        self.batch_size = batch_size
        self.opinion_limit = opinion_limit

    def _summarize_batch(
        self,
        opinions: list[AgentOpinion],
        batch_number: int,
    ) -> str:

        items = []

        for opinion in opinions:

            if not opinion.success:
                continue

            items.append(
                f"""
AGENT: {opinion.agent_id}
SPECIALTY: {opinion.specialty}
PERSPECTIVE: {opinion.perspective}

OPINION:
{opinion.content[:self.opinion_limit]}
"""
            )

        system = """
You are the XenoCode Consensus Analyst.

Analyze independent engineering proposals.

Identify:
- Strong technical ideas.
- Shared conclusions.
- Genuine disagreements.
- Unique insights.
- Weak assumptions.
- Technical risks.
- Open questions.

Do not treat repetition as proof.
Preserve valuable minority opinions.
Never invent evidence or benchmark results.

Produce a concise structured synthesis.
"""

        response = self.provider.chat(
            [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": (
                        f"CONSENSUS BATCH {batch_number}\n\n"
                        + "\n".join(items)
                    ),
                },
            ],
            model=self.model,
        )

        content = response.get("content")

        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("Empty batch synthesis.")

        return content.strip()

    def synthesize(
        self,
        opinions: list[AgentOpinion],
    ) -> str:

        successful = [
            opinion for opinion in opinions
            if opinion.success
        ]

        if not successful:
            raise RuntimeError("No successful agent opinions.")

        batches = [
            successful[i:i + self.batch_size]
            for i in range(0, len(successful), self.batch_size)
        ]

        summaries = []

        for index, batch in enumerate(batches, 1):

            try:
                summary = self._summarize_batch(
                    batch,
                    index,
                )

            except Exception as exc:

                summary = (
                    f"BATCH {index} SYNTHESIS FAILED: "
                    f"{type(exc).__name__}: {exc}\n"
                    "Available raw findings:\n"
                )

                for opinion in batch:
                    if opinion.success:
                        summary += (
                            f"\n[{opinion.agent_id} / "
                            f"{opinion.specialty}]\n"
                            + opinion.content[:500]
                        )

            summaries.append(summary)

        final_system = """
You are XENO MASTER ENGINEER.

Turn independent engineering analyses into one coherent design.

You must:

1. Compare all batch syntheses.
2. Resolve contradictions using technical reasoning.
3. Preserve strong minority solutions when justified.
4. Reject unsupported claims.
5. Avoid unnecessary complexity.
6. Consider performance, memory and scalability.
7. Prioritize correctness, maintainability and security.
8. Produce one unified engineering proposal.

OUTPUT:

# FINAL ENGINEERING DESIGN

## Recommended Architecture

## Implementation Strategy

## Best Ideas Incorporated

## Rejected Alternatives and Reasons

## Performance Considerations

## Mathematical and Algorithmic Considerations

## Security Considerations

## Testing Strategy

## Remaining Risks

## Final Recommendation

Do not claim code has been implemented.
Do not invent successful test results.
"""

        try:

            response = self.provider.chat(
                [
                    {
                        "role": "system",
                        "content": final_system,
                    },
                    {
                        "role": "user",
                        "content": (
                            "SYNTHESIS OF THE SWARM:\n\n"
                            + "\n\n".join(
                                f"BATCH {i + 1}\n{summary}"
                                for i, summary in enumerate(summaries)
                            )
                        ),
                    },
                ],
                model=self.model,
            )

            result = response.get("content")

            if isinstance(result, str) and result.strip():
                return result.strip()

            raise RuntimeError("Empty final synthesis.")

        except Exception as exc:

            return (
                "# CONSENSUS FALLBACK\n\n"
                "The final AI synthesis could not be completed.\n"
                f"Reason: {type(exc).__name__}: {exc}\n\n"
                "The following batch analyses are preserved:\n\n"
                + "\n\n".join(summaries)
            )
