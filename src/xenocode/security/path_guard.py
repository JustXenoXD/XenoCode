"""Workspace path validation and secret-file protection."""

import os
from pathlib import Path


IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".ssh", ".aws", ".config",
    ".xenocode", "dist", "build",
}

SECRET_NAMES = {
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
    ".html", ".css", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".md", ".txt", ".xml",
    ".lua", ".sql", ".sh", ".gd",
}

SPECIAL_FILES = {
    "Dockerfile", "Makefile", "LICENSE",
    "NOTICE", ".gitignore",
}


class PathViolation(ValueError):
    """Raised when a workspace path violates security rules."""


class PathGuard:

    def __init__(self, workspace):
        self.root = Path(workspace).expanduser().resolve()

        if not self.root.is_dir():
            raise PathViolation("Workspace does not exist.")

    @staticmethod
    def _sensitive(name):
        lower = name.lower()

        return (
            lower in SECRET_NAMES
            or lower.startswith(".env")
            or Path(lower).suffix in SECRET_SUFFIXES
        )

    def is_text_file(self, path):
        return (
            path.name in SPECIAL_FILES
            or path.suffix.lower() in TEXT_SUFFIXES
        )

    def resolve(self, relative, must_exist=False):
        if not isinstance(relative, str) or not relative.strip():
            raise PathViolation("Invalid empty path.")

        raw = Path(relative)

        if raw.is_absolute():
            raise PathViolation("Absolute paths are not allowed.")

        parts = [part for part in raw.parts if part != "."]

        if ".." in parts:
            raise PathViolation("Path traversal is not allowed.")

        for part in parts:
            if part in IGNORED_DIRS or self._sensitive(part):
                raise PathViolation(
                    f"Access to protected path is forbidden: {part}"
                )

        candidate = self.root.joinpath(*parts)

        current = self.root

        for part in parts:
            current = current / part

            if current.is_symlink():
                raise PathViolation("Symbolic links are not allowed.")

        resolved = candidate.resolve(strict=False)

        if not resolved.is_relative_to(self.root):
            raise PathViolation("Path escapes the workspace.")

        if must_exist and not resolved.exists():
            raise FileNotFoundError(relative)

        return resolved

    def iter_files(self, relative=".", limit=200):
        folder = self.resolve(relative, must_exist=True)

        if not folder.is_dir():
            raise PathViolation("Expected a directory.")

        count = 0

        for current, directories, filenames in os.walk(
            folder,
            topdown=True,
            followlinks=False,
        ):
            base = Path(current)

            directories[:] = sorted(
                name for name in directories
                if name not in IGNORED_DIRS
                and not self._sensitive(name)
                and not (base / name).is_symlink()
            )

            for name in sorted(filenames):
                candidate = base / name

                if candidate.is_symlink():
                    continue

                relative_path = candidate.relative_to(
                    self.root
                ).as_posix()

                try:
                    safe = self.resolve(
                        relative_path,
                        must_exist=True,
                    )

                    if not safe.is_file():
                        continue

                    if not self.is_text_file(safe):
                        continue

                    if safe.stat().st_size > 120_000:
                        continue

                except (OSError, PathViolation):
                    continue

                yield safe

                count += 1

                if count >= limit:
                    return
