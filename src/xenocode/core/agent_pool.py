"""Bounded concurrent execution for XenoCode agents."""

from concurrent.futures import ThreadPoolExecutor, as_completed

from xenocode.agents.swarm_worker import AgentOpinion


class AgentPool:

    MAX_AGENTS = 500
    MAX_WORKERS = 8

    def __init__(self, max_workers: int = 1):

        if type(max_workers) is not int:
            raise ValueError("Worker count must be an integer.")

        if not 1 <= max_workers <= self.MAX_WORKERS:
            raise ValueError("Concurrency must be between 1 and 8.")

        self.max_workers = max_workers

    def execute(
        self,
        worker,
        assignments,
        task: str,
        context: str,
    ) -> list[AgentOpinion]:

        if len(assignments) > self.MAX_AGENTS:
            raise ValueError("Maximum agent count exceeded.")

        if not assignments:
            return []

        results = []

        with ThreadPoolExecutor(
            max_workers=min(
                self.max_workers,
                len(assignments),
            ),
            thread_name_prefix="xeno-agent",
        ) as executor:

            futures = {
                executor.submit(
                    worker.run,
                    assignment,
                    task,
                    context,
                ): assignment
                for assignment in assignments
            }

            for future in as_completed(futures):

                assignment = futures[future]

                try:
                    result = future.result()

                except Exception as exc:
                    result = AgentOpinion(
                        agent_id=assignment.agent_id,
                        specialty=assignment.specialty,
                        perspective=assignment.perspective,
                        success=False,
                        content="",
                        error=f"{type(exc).__name__}: {exc}",
                    )

                results.append(result)

        results.sort(key=lambda item: item.agent_id)

        return results
