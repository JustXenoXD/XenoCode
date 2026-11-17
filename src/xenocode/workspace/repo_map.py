"""Repository structure and dependency-map generation."""

from pathlib import PurePosixPath

from xenocode.workspace.indexer import WorkspaceIndex


class RepositoryMapBuilder:

    def __init__(
        self,
        max_output_chars: int = 24000,
        max_symbols: int = 300,
    ):
        if (
            type(max_output_chars) is not int
            or not 256 <= max_output_chars <= 200000
        ):
            raise ValueError("Invalid repository map output limit.")

        if (
            type(max_symbols) is not int
            or not 1 <= max_symbols <= 5000
        ):
            raise ValueError("Invalid symbol limit.")

        self.max_output_chars = max_output_chars
        self.max_symbols = max_symbols

    @staticmethod
    def _build_tree(index: WorkspaceIndex):
        tree = {}

        for record in index.files:
            node = tree
            parts = PurePosixPath(record.path).parts

            for part in parts[:-1]:
                node = node.setdefault(part, {})

            node[parts[-1]] = None

        lines = []

        def render(node, depth=0):
            for name in sorted(node):
                child = node[name]
                is_directory = isinstance(child, dict)

                suffix = "/" if is_directory else ""
                lines.append(
                    f"{'  ' * depth}- {name}{suffix}"
                )

                if is_directory:
                    render(child, depth + 1)

        render(tree)
        return lines

    def build(self, index: WorkspaceIndex) -> str:
        if not isinstance(index, WorkspaceIndex):
            raise TypeError("Expected a WorkspaceIndex.")

        lines = [
            f"# Repository Map: {index.root_name}",
            "",
            f"Files indexed: {index.file_count}",
            f"Total indexed bytes: {index.total_bytes}",
            f"Files skipped: {index.skipped_files}",
            f"Index truncated: {index.truncated}",
            "",
            "## Languages",
        ]

        for language, count in index.language_counts.items():
            lines.append(f"- {language}: {count}")

        lines.extend([
            "",
            "## Project Structure",
        ])

        lines.extend(self._build_tree(index))

        lines.extend([
            "",
            "## Python Modules",
        ])

        remaining = self.max_symbols

        python_files = [
            item
            for item in index.files
            if item.language == "Python"
        ]

        for item in python_files[:200]:
            lines.append(f"\n### {item.path}")

            if item.parse_error:
                lines.append("- Parsing failed.")
                continue

            if item.imports:
                lines.append(
                    "- Imports: " + ", ".join(item.imports)
                )

            for symbol in item.symbols:
                if remaining <= 0:
                    lines.append("- Symbol output limit reached.")
                    break

                lines.append(
                    f"- {symbol.kind}: {symbol.name} "
                    f"(line {symbol.line})"
                )
                remaining -= 1

            if remaining <= 0:
                break

        result = "\n".join(lines)

        if len(result) > self.max_output_chars:
            marker = "\n...[REPOSITORY MAP TRUNCATED]"
            result = (
                result[:self.max_output_chars - len(marker)]
                + marker
            )

        return result
