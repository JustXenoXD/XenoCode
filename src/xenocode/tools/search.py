"""Bounded text search across workspace files."""

from xenocode.security.path_guard import PathGuard


class SearchTools:

    def __init__(self, guard: PathGuard):
        self.guard = guard

    def search_text(
        self,
        query: str,
        path: str = ".",
        max_results: int = 20,
    ) -> str:

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Search query cannot be empty.")

        if len(query) > 500:
            raise ValueError("Search query is too long.")

        if type(max_results) is not int or not 1 <= max_results <= 50:
            raise ValueError("max_results must be between 1 and 50.")

        results = []
        needle = query.casefold()

        for file in self.guard.iter_files(path):
            try:
                with file.open(
                    "r",
                    encoding="utf-8",
                    errors="replace",
                ) as handle:

                    for line_number, line in enumerate(handle, 1):
                        if needle not in line.casefold():
                            continue

                        relative = file.relative_to(
                            self.guard.root
                        ).as_posix()

                        results.append(
                            f"{relative}:{line_number}: "
                            f"{line.strip()[:300]}"
                        )

                        if len(results) >= max_results:
                            return "\n".join(results)

            except OSError:
                continue

        return "\n".join(results) if results else "No matches found."
