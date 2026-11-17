"""Controlled filesystem operations."""

from xenocode.security.path_guard import PathGuard


class FileSystemTools:

    def __init__(self, guard: PathGuard):
        self.guard = guard

    def read_file(self, path: str) -> str:
        target = self.guard.resolve(
            path,
            must_exist=True,
        )

        if not target.is_file():
            raise ValueError("Path is not a file.")

        if not self.guard.is_text_file(target):
            raise ValueError("Unsupported file type.")

        if target.stat().st_size > 100_000:
            raise ValueError("File exceeds the size limit.")

        try:
            return target.read_text(encoding="utf-8")
        except UnicodeError as exc:
            raise ValueError("File is not valid UTF-8.") from exc

    def list_files(self, path: str = ".") -> str:
        files = [
            item.relative_to(self.guard.root).as_posix()
            for item in self.guard.iter_files(path)
        ]

        return "\n".join(files) if files else "No files found."

    def write_file(
        self,
        path: str,
        content: str,
        overwrite: bool = False,
    ) -> str:

        if not isinstance(content, str):
            raise ValueError("Content must be text.")

        if type(overwrite) is not bool:
            raise ValueError("Overwrite must be a boolean.")

        if len(content.encode("utf-8")) > 100_000:
            raise ValueError("Content exceeds the size limit.")

        target = self.guard.resolve(path)

        if not self.guard.is_text_file(target):
            raise ValueError("Unsupported file type.")

        parent_relative = target.parent.relative_to(
            self.guard.root
        ).as_posix() or "."

        parent = self.guard.resolve(
            parent_relative,
            must_exist=True,
        )

        if not parent.is_dir():
            raise ValueError("Parent directory does not exist.")

        if target.exists() and not overwrite:
            raise FileExistsError(
                "File exists. Explicit overwrite is required."
            )

        if target.exists() and not target.is_file():
            raise ValueError("Target is not a regular file.")

        target.write_text(content, encoding="utf-8")

        return (
            f"Successfully wrote {target.relative_to(self.guard.root)} "
            f"({len(content)} characters)."
        )
