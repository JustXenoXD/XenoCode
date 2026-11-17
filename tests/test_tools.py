import tempfile
import unittest

from pathlib import Path

from xenocode.security.path_guard import PathGuard, PathViolation
from xenocode.tools.registry import (
    ApprovalDenied,
    build_default_registry,
)


class ToolTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

        (self.root / "README.md").write_text(
            "# XenoCode test",
            encoding="utf-8",
        )

        self.registry = build_default_registry(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_path_traversal_rejected(self):
        guard = PathGuard(self.root)

        with self.assertRaises(PathViolation):
            guard.resolve("../outside.txt")

    def test_secret_file_blocked(self):
        (self.root / ".env").write_text(
            "SECRET=value",
            encoding="utf-8",
        )

        with self.assertRaises(PathViolation):
            self.registry.execute(
                "read_file",
                {"path": ".env"},
            )

    def test_read_file(self):
        result = self.registry.execute(
            "read_file",
            {"path": "README.md"},
        )

        self.assertIn("XenoCode", result)

    def test_write_requires_approval(self):

        with self.assertRaises(ApprovalDenied):
            self.registry.execute(
                "write_file",
                {
                    "path": "new.py",
                    "content": "print('hello')",
                },
            )

        self.assertFalse(
            (self.root / "new.py").exists()
        )

    def test_approved_write(self):

        result = self.registry.execute(
            "write_file",
            {
                "path": "new.py",
                "content": "print('hello')",
            },
            approval=lambda name, args: True,
        )

        self.assertIn("Successfully wrote", result)

        self.assertEqual(
            (self.root / "new.py").read_text(),
            "print('hello')",
        )

    def test_overwrite_protection(self):

        with self.assertRaises(FileExistsError):
            self.registry.execute(
                "write_file",
                {
                    "path": "README.md",
                    "content": "Replacement",
                },
                approval=lambda name, args: True,
            )

    def test_search_text(self):

        result = self.registry.execute(
            "search_text",
            {"query": "XenoCode"},
        )

        self.assertIn("README.md", result)

    def test_unknown_tool(self):

        with self.assertRaises(Exception):
            self.registry.execute(
                "delete_everything",
                {},
            )

    def test_invalid_arguments(self):

        with self.assertRaises(Exception):
            self.registry.execute(
                "read_file",
                {"path": "README.md", "unexpected": True},
            )


    def test_run_tests_requires_approval(self):
        with self.assertRaises(ApprovalDenied):
            self.registry.execute("run_tests", {})

        with self.assertRaises(ApprovalDenied):
            self.registry.execute(
                "run_tests",
                {},
                approval=lambda name, args: False,
            )

    def test_read_file_does_not_require_approval(self):
        result = self.registry.execute(
            "read_file",
            {"path": "README.md"},
            approval=lambda name, args: False,
        )

        self.assertIn("XenoCode", result)


if __name__ == "__main__":
    unittest.main()
