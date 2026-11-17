"""Safe, bounded project context collection."""

import os
from pathlib import Path


IGNORED = {
    ".git", ".venv", "venv", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".xenocode", ".ssh", ".aws",
    ".secrets", ".config", "dist", "build",
}

SECRET_NAMES = {
    ".env", ".env.local", ".env.production",
    "credentials.json", "secrets.json",
    "id_rsa", "id_ed25519", "token.txt",
}

SECRET_SUFFIXES = {
    ".pem", ".key", ".p12", ".pfx", ".keystore",
}

TEXT_SUFFIXES = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".kt", ".go", ".rs", ".cpp",
    ".c", ".h", ".cs", ".rb", ".swift",
    ".html", ".css", ".json", ".yaml",
    ".yml", ".toml", ".ini", ".md",
    ".txt", ".xml", ".lua", ".sql",
    ".sh", ".gd",
}

IMPORTANT_FILES = {
    "README.md", "pyproject.toml",
    "package.json", "Cargo.toml",
    "go.mod", "requirements.txt",
}


class ContextError(RuntimeError):
    pass


class ProjectContextBuilder:

    def __init__(
        self,
        workspace: str | Path,
        max_files: int = 120,
        max_chars: int = 24000,
    ):
        self.root = Path(workspace).expanduser().resolve()
        self.max_files = max_files
        self.max_chars = max_chars

        if not self.root.is_dir():
            raise ContextError("Workspace directory does not exist.")

    def _safe_file(self, path: Path) -> bool:
        if path.is_symlink():
            return False

        if path.name.lower() in SECRET_NAMES:
            return False

        if path.suffix.lower() in SECRET_SUFFIXES:
            return False

        if path.name.lower().startswith(".env."):
            return False

        return (
            path.suffix.lower() in TEXT_SUFFIXES
            or path.name in {"Dockerfile", "Makefile"}
        )

    def collect_files(self) -> list[Path]:
        files = []

        for current, directories, names in os.walk(
            self.root,
            followlinks=False,
        ):
            directories[:] = [
                name for name in directories
                if name not in IGNORED
                and not (Path(current) / name).is_symlink()
            ]

            for name in sorted(names):
                path = Path(current) / name

                if not self._safe_file(path):
                    continue

                try:
                    if path.stat().st_size > 120000:
                        continue
                except OSError:
                    continue

                files.append(path)

                if len(files) >= self.max_files:
                    return files

        return files

    def build(self) -> str:
        files = self.collect_files()

        relative = [
            path.relative_to(self.root).as_posix()
            for path in files
        ]

        output = [
            f"PROJECT: {self.root.name}",
            f"ROOT: {self.root}",
            f"INDEXED FILES: {len(files)}",
            "",
            "PROJECT STRUCTURE:",
            *relative,
            "",
            "SELECTED FILE CONTENTS:",
        ]

        priority = sorted(
            files,
            key=lambda path: (
                0 if path.name in IMPORTANT_FILES else 1,
                len(path.parts),
                str(path),
            ),
        )

        remaining = self.max_chars

        for path in priority:
            if remaining <= 0:
                break

            try:
                content = path.read_text(
                    encoding="utf-8"
                )
            except (OSError, UnicodeError):
                continue

            excerpt = content[:min(2400, remaining)]

            label = path.relative_to(
                self.root
            ).as_posix()

            block = f"\n--- {label} ---\n{excerpt}\n"

            output.append(block)
            remaining -= len(block)

        return "\n".join(output)
