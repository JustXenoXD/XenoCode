import tempfile
import unittest

from pathlib import Path

from xenocode.tools.registry import build_default_registry
from xenocode.workspace.indexer import (
    WorkspaceIndexer,
    WorkspaceIndexError,
)
from xenocode.workspace.repo_map import RepositoryMapBuilder


class WorkspaceIndexerTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

        self.module = self.root / "src" / "example.py"
        self.module.parent.mkdir(parents=True)

        self.module.write_text(
            "import os\n"
            "from pathlib import Path\n"
            "\n"
            "class Example:\n"
            "    def run(self):\n"
            "        return True\n"
            "\n"
            "def main():\n"
            "    pass\n",
            encoding="utf-8",
        )

        (self.root / "README.md").write_text(
            "# Example project",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_index_files(self):
        index = WorkspaceIndexer(self.root).build()

        self.assertGreaterEqual(index.file_count, 2)
        self.assertIn("src/example.py", [
            item.path for item in index.files
        ])

    def test_extract_python_imports(self):
        index = WorkspaceIndexer(self.root).build()

        module = next(
            item for item in index.files
            if item.path == "src/example.py"
        )

        self.assertIn("os", module.imports)
        self.assertIn("pathlib", module.imports)

    def test_extract_python_symbols(self):
        index = WorkspaceIndexer(self.root).build()

        module = next(
            item for item in index.files
            if item.path == "src/example.py"
        )

        names = {item.name for item in module.symbols}

        self.assertIn("Example", names)
        self.assertIn("run", names)
        self.assertIn("main", names)

    def test_sensitive_files_excluded(self):
        (self.root / ".env").write_text(
            "SECRET=value",
            encoding="utf-8",
        )

        (self.root / "secrets.json").write_text(
            '{"secret": "value"}',
            encoding="utf-8",
        )

        index = WorkspaceIndexer(self.root).build()
        paths = {item.path for item in index.files}

        self.assertNotIn(".env", paths)
        self.assertNotIn("secrets.json", paths)

    def test_file_limit(self):
        for name in ("a.py", "b.py", "c.py"):
            (self.root / name).write_text(
                "value = 1",
                encoding="utf-8",
            )

        index = WorkspaceIndexer(
            self.root,
            max_files=2,
        ).build()

        self.assertEqual(index.file_count, 2)
        self.assertTrue(index.truncated)

    def test_file_size_limit(self):
        index = WorkspaceIndexer(
            self.root,
            max_file_bytes=10,
        ).build()

        self.assertLess(index.file_count, 2)
        self.assertGreater(index.skipped_files, 0)

    def test_total_size_limit(self):
        index = WorkspaceIndexer(
            self.root,
            max_total_bytes=10,
        ).build()

        self.assertTrue(index.truncated)
        self.assertLessEqual(index.total_bytes, 10)

    def test_invalid_python_is_recorded(self):
        (self.root / "broken.py").write_text(
            "def invalid(:\n",
            encoding="utf-8",
        )

        index = WorkspaceIndexer(self.root).build()

        broken = next(
            item for item in index.files
            if item.path == "broken.py"
        )

        self.assertTrue(broken.parse_error)

    def test_index_configuration_validation(self):
        with self.assertRaises(WorkspaceIndexError):
            WorkspaceIndexer(self.root, max_files=0)

        with self.assertRaises(WorkspaceIndexError):
            WorkspaceIndexer(self.root, max_file_bytes=0)

        with self.assertRaises(WorkspaceIndexError):
            WorkspaceIndexer(self.root, max_total_bytes=0)


class RepositoryMapTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

        package = self.root / "src" / "sample"
        package.mkdir(parents=True)

        (package / "main.py").write_text(
            "import json\n"
            "class Application:\n"
            "    pass\n",
            encoding="utf-8",
        )

        (self.root / "README.md").write_text(
            "# Sample",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_repository_map_contains_structure(self):
        index = WorkspaceIndexer(self.root).build()
        result = RepositoryMapBuilder().build(index)

        self.assertIn("Repository Map", result)
        self.assertIn("src/", result)
        self.assertIn("main.py", result)
        self.assertIn("Python", result)

    def test_repository_map_contains_symbols(self):
        index = WorkspaceIndexer(self.root).build()
        result = RepositoryMapBuilder().build(index)

        self.assertIn("Application", result)
        self.assertIn("json", result)

    def test_repository_map_output_limit(self):
        index = WorkspaceIndexer(self.root).build()

        result = RepositoryMapBuilder(
            max_output_chars=256,
        ).build(index)

        self.assertLessEqual(len(result), 256)
        self.assertIn("TRUNCATED", result)

    def test_invalid_repository_map_input(self):
        with self.assertRaises(TypeError):
            RepositoryMapBuilder().build("invalid")

    def test_repository_map_tool(self):
        registry = build_default_registry(self.root)

        result = registry.execute(
            "get_repository_map",
            {},
        )

        self.assertIn("Repository Map", result)
        self.assertIn("main.py", result)


if __name__ == "__main__":
    unittest.main()
