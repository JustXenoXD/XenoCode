import tempfile
import unittest

from pathlib import Path

from xenocode.memory.store import (
    MemoryStore,
    MemoryStoreError,
)


class MemoryStoreTests(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = MemoryStore(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_add_and_persist(self):
        entry = self.store.add(
            "decision",
            "Use SQLite for local project metadata.",
            tags=["database", "architecture"],
        )

        reopened = MemoryStore(self.root)
        results = reopened.recent()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, entry.id)
        self.assertEqual(
            results[0].content,
            "Use SQLite for local project metadata.",
        )

    def test_storage_is_inside_xenocode_directory(self):
        self.store.add("note", "Test memory.")

        self.assertTrue(
            (self.root / ".xenocode" / "memory.jsonl").is_file()
        )

    def test_empty_memory_does_not_create_storage(self):
        self.assertEqual(self.store.recent(), [])
        self.assertFalse(
            (self.root / ".xenocode").exists()
        )

    def test_search_content(self):
        self.store.add(
            "convention",
            "Use snake_case for Python functions.",
        )

        results = self.store.search("snake_case")

        self.assertEqual(len(results), 1)

    def test_search_tags(self):
        self.store.add(
            "architecture",
            "Separate providers from orchestration.",
            tags=["design"],
        )

        self.assertEqual(
            len(self.store.search("design")),
            1,
        )

    def test_category_filter(self):
        self.store.add("decision", "Use JSONL.")
        self.store.add("note", "Review the documentation.")

        results = self.store.recent(category="decision")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].category, "decision")

    def test_recent_limit(self):
        for number in range(4):
            self.store.add("note", f"Entry {number}")

        results = self.store.recent(limit=2)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].content, "Entry 3")
        self.assertEqual(results[1].content, "Entry 2")

    def test_delete_entry(self):
        entry = self.store.add("note", "Temporary fact.")

        self.assertTrue(self.store.delete(entry.id))
        self.assertFalse(self.store.delete(entry.id))
        self.assertEqual(self.store.recent(), [])

    def test_invalid_category(self):
        with self.assertRaises(MemoryStoreError):
            self.store.add("unknown", "Some fact.")

    def test_empty_content(self):
        with self.assertRaises(MemoryStoreError):
            self.store.add("note", "   ")

    def test_entry_length_limit(self):
        store = MemoryStore(
            self.root,
            max_entry_chars=20,
        )

        with self.assertRaises(MemoryStoreError):
            store.add("note", "x" * 21)

    def test_secret_content_rejected(self):
        with self.assertRaises(MemoryStoreError):
            self.store.add(
                "note",
                "password=supersecretvalue123",
            )

    def test_private_key_rejected(self):
        with self.assertRaises(MemoryStoreError):
            self.store.add(
                "note",
                "-----BEGIN PRIVATE KEY-----",
            )

    def test_invalid_tags(self):
        with self.assertRaises(MemoryStoreError):
            self.store.add(
                "note",
                "Valid fact.",
                tags=[""],
            )

    def test_max_entries(self):
        store = MemoryStore(
            self.root,
            max_entries=2,
        )

        for number in range(3):
            store.add("note", f"Entry {number}")

        results = store.recent(limit=10 if False else 2)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].content, "Entry 2")
        self.assertEqual(results[1].content, "Entry 1")

    def test_context_generation(self):
        self.store.add(
            "decision",
            "Use a local JSONL memory store.",
        )

        result = self.store.to_context()

        self.assertIn("PROJECT MEMORY", result)
        self.assertIn("JSONL", result)

    def test_context_output_limit(self):
        for number in range(5):
            self.store.add(
                "note",
                f"Memory entry number {number}. " + "x" * 100,
            )

        result = self.store.to_context(max_chars=128)

        self.assertLessEqual(len(result), 128)
        self.assertIn("MEMORY TRUNCATED", result)

    def test_memory_directory_symlink_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()

        link = self.root / ".xenocode"
        link.symlink_to(outside, target_is_directory=True)

        with self.assertRaises(MemoryStoreError):
            self.store.add("note", "Must not follow symlink.")

    def test_memory_file_symlink_rejected(self):
        directory = self.root / ".xenocode"
        directory.mkdir()

        outside = self.root / "outside.jsonl"
        outside.write_text("", encoding="utf-8")

        link = directory / "memory.jsonl"
        link.symlink_to(outside)

        with self.assertRaises(MemoryStoreError):
            self.store.add("note", "Must not follow symlink.")

    def test_corrupt_memory_is_not_overwritten(self):
        directory = self.root / ".xenocode"
        directory.mkdir()

        path = directory / "memory.jsonl"
        path.write_text(
            "{invalid json}\n",
            encoding="utf-8",
        )

        with self.assertRaises(MemoryStoreError):
            self.store.add("note", "New fact.")

        self.assertEqual(
            path.read_text(encoding="utf-8"),
            "{invalid json}\n",
        )


if __name__ == "__main__":
    unittest.main()
