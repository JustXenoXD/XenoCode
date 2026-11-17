"""Controlled Python unittest execution."""

import os
import subprocess
import sys

from xenocode.security.path_guard import PathGuard


class TestRunner:

    def __init__(self, guard: PathGuard):
        self.guard = guard

    def run_tests(self, timeout: int = 90) -> str:

        if type(timeout) is not int or not 1 <= timeout <= 180:
            raise ValueError("Timeout must be between 1 and 180 seconds.")

        test_directory = self.guard.resolve(
            "tests",
            must_exist=True,
        )

        if not test_directory.is_dir():
            raise ValueError("Tests directory does not exist.")

        source_directory = self.guard.root / "src"

        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": str(source_directory),
            "PYTHONIOENCODING": "utf-8",
        }

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "tests",
                    "-v",
                ],
                cwd=str(self.guard.root),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
                check=False,
                shell=False,
            )

        except subprocess.TimeoutExpired:
            return f"TEST ERROR: Timeout after {timeout} seconds."

        output = result.stdout + "\n" + result.stderr

        return (
            f"EXIT CODE: {result.returncode}\n"
            f"RESULT:\n{output[-12000:]}"
        )
