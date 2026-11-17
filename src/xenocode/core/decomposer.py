"""Creates diverse assignments for the XenoCode agent swarm."""

from dataclasses import dataclass


SPECIALTIES = (
    ("Architect", "system architecture and component design"),
    ("Algorithmist", "algorithms, data structures and complexity"),
    ("Mathematician", "mathematical correctness and optimization"),
    ("Security", "security, trust boundaries and threat analysis"),
    ("Performance", "latency, memory and computational efficiency"),
    ("Testing", "testing strategies and edge cases"),
    ("Reliability", "fault tolerance and error recovery"),
    ("Maintainer", "readability and long-term maintainability"),
    ("Innovator", "unconventional and creative alternatives"),
    ("Auditor", "assumptions, contradictions and technical risks"),
)

PERSPECTIVES = (
    "Conservative: prioritize proven, low-risk engineering.",
    "Performance-first: minimize computational overhead.",
    "Reliability-first: prioritize predictable behavior.",
    "Simplicity-first: minimize unnecessary complexity.",
    "Scalability-first: consider large projects and workloads.",
    "Adversarial: actively search for weaknesses.",
    "Alternative-design: explore a fundamentally different approach.",
    "Mathematical: formalize assumptions and correctness.",
    "Resource-aware: consider limited RAM and CPU.",
    "Future-oriented: consider extensibility and future requirements.",
)


@dataclass(frozen=True)
class AgentAssignment:
    agent_id: str
    specialty: str
    focus: str
    perspective: str


class TaskDecomposer:

    MAX_AGENTS = 500

    @classmethod
    def create_assignments(
        cls,
        agent_count: int,
    ) -> list[AgentAssignment]:

        if type(agent_count) is not int:
            raise ValueError("Agent count must be an integer.")

        if not 1 <= agent_count <= cls.MAX_AGENTS:
            raise ValueError("Agent count must be between 1 and 500.")

        assignments = []

        for index in range(agent_count):

            specialty, focus = SPECIALTIES[
                index % len(SPECIALTIES)
            ]

            perspective_index = (
                index // len(SPECIALTIES)
            ) % len(PERSPECTIVES)

            variant = (
                index // (
                    len(SPECIALTIES) * len(PERSPECTIVES)
                )
            ) + 1

            perspective = (
                PERSPECTIVES[perspective_index]
                + f"\nIndependent exploration variant: {variant}."
                + "\nSeek a distinct hypothesis and avoid generic repetition."
            )

            assignments.append(
                AgentAssignment(
                    agent_id=f"XENO-{index + 1:03d}",
                    specialty=specialty,
                    focus=focus,
                    perspective=perspective,
                )
            )

        return assignments
