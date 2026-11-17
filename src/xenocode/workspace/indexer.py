"""Bounded and security-aware workspace indexing."""

import ast
import hashlib

from dataclasses import dataclass
from pathlib import Path

from xenocode.security.path_guard import PathGuard


class WorkspaceIndexError(ValueError):
    """Raised when workspace indexing configuration is invalid."""


LANGUAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".kt": "Kotlin",
    ".go": "Go",
    ".rs": "Rust",
    ".cpp": "C++",
    ".c": "C",
    ".h": "C/C++",
    ".cs": "C#",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".html": "HTML",
    ".css": "CSS",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".toml": "TOML",
    ".ini": "INI",
    ".md": "Markdown",
    ".txt": "Text",
    ".xml": "XML",
    ".lua": "Lua",
    ".sql": "SQL",
    ".sh": "Shell",
    ".gd": "GDScript",
}


@dataclass(frozen=True)
class IndexedSymbol:
    name: str
    kind: str
    line: int


@dataclass(frozen=True)
class IndexedFile:
    path: str
    size_bytes: int
    language: str
    sha256: str
    imports: tuple[str, ...] = ()
    symbols: tuple[IndexedSymbol, ...] = ()
    parse_error: bool = False


@dataclass(frozen=True)
class WorkspaceIndex:
    root_name: str
    files: tuple[IndexedFile, ...]
    total_bytes: int
    truncated: bool
    skipped_files: int

    @property
    def file_count(self) -> int:
        return len(self.files)

    @property
    def language_counts(self) -> dict[str, int]:
        counts = {}

        for item in self.files:
            counts[item.language] = (
                counts.get(item.language, 0) + 1
            )

        return dict(sorted(counts.items()))

    def to_dict(self) -> dict:
        return {
            "root_name": self.root_name,
            "file_count": self.file_count,
            "total_bytes": self.total_bytes,
            "truncated": self.truncated,
            "skipped_files": self.skipped_files,
            "language_counts": self.language_counts,
            "files": [
                {
                    "path": item.path,
                    "size_bytes": item.size_bytes,
                    "language": item.language,
                    "sha256": item.sha256,
                    "imports": list(item.imports),
                    "symbols": [
                        {
                            "name": symbol.name,
                            "kind": symbol.kind,
                            "line": symbol.line,
                        }
                        for symbol in item.symbols
                    ],
                    "parse_error": item.parse_error,
                }
                for item in self.files
            ],
        }


class WorkspaceIndexer:

    def __init__(
        self,
        workspace: str | Path,
        max_files: int = 500,
        max_file_bytes: int = 120000,
        max_total_bytes: int = 5000000,
    ):
        for name, value, minimum, maximum in (
            ("max_files", max_files, 1, 5000),
            ("max_file_bytes", max_file_bytes, 1, 120000),
            ("max_total_bytes", max_total_bytes, 1, 50000000),
        ):
            if type(value) is not int or not minimum <= value <= maximum:
                raise WorkspaceIndexError(
                    f"Invalid {name} limit."
                )

        self.guard = PathGuard(workspace)
        self.max_files = max_files
        self.max_file_bytes = max_file_bytes
        self.max_total_bytes = max_total_bytes

    @staticmethod
    def _language(path: Path) -> str:
        if path.name in {"Dockerfile", "Makefile"}:
            return "Build"

        return LANGUAGES.get(
            path.suffix.lower(),
            "Other",
        )

    @staticmethod
    def _python_metadata(content: str):
        try:
            tree = ast.parse(content)
        except (SyntaxError, ValueError, RecursionError):
            return (), (), True

        imports = set()
        symbols = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)

            elif isinstance(node, ast.ImportFrom):
                prefix = "." * node.level
                imports.add(prefix + (node.module or ""))

            elif isinstance(node, ast.ClassDef):
                symbols.append(
                    IndexedSymbol(
                        node.name,
                        "class",
                        node.lineno,
                    )
                )

            elif isinstance(node, ast.AsyncFunctionDef):
                symbols.append(
                    IndexedSymbol(
                        node.name,
                        "async_function",
                        node.lineno,
                    )
                )

            elif isinstance(node, ast.FunctionDef):
                symbols.append(
                    IndexedSymbol(
                        node.name,
                        "function",
                        node.lineno,
                    )
                )

        return (
            tuple(sorted(imports)),
            tuple(sorted(
                symbols,
                key=lambda item: (item.line, item.kind, item.name),
            )),
            False,
        )

    def build(self) -> WorkspaceIndex:
        records = []
        total_bytes = 0
        skipped = 0
        truncated = False

        candidates = self.guard.iter_files(
            limit=self.max_files + 1
        )

        for position, path in enumerate(candidates):
            if position >= self.max_files:
                truncated = True
                break

            try:
                raw = path.read_bytes()
            except OSError:
                skipped += 1
                continue

            size = len(raw)

            if size > self.max_file_bytes:
                skipped += 1
                continue

            if total_bytes + size > self.max_total_bytes:
                skipped += 1
                truncated = True
                break

            try:
                content = raw.decode("utf-8")
            except UnicodeDecodeError:
                skipped += 1
                continue

            relative = path.relative_to(
                self.guard.root
            ).as_posix()

            imports = ()
            symbols = ()
            parse_error = False

            if path.suffix.lower() == ".py":
                imports, symbols, parse_error = (
                    self._python_metadata(content)
                )

            records.append(
                IndexedFile(
                    path=relative,
                    size_bytes=size,
                    language=self._language(path),
                    sha256=hashlib.sha256(raw).hexdigest(),
                    imports=imports,
                    symbols=symbols,
                    parse_error=parse_error,
                )
            )

            total_bytes += size

        return WorkspaceIndex(
            root_name=self.guard.root.name,
            files=tuple(records),
            total_bytes=total_bytes,
            truncated=truncated,
            skipped_files=skipped,
        )
