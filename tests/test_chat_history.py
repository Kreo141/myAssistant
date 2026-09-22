import tempfile
import unittest
from pathlib import Path

from core.exceptions import StorageError
from storage.chat_history import ChatHistoryRepository


class ChatHistoryRepositoryTests(unittest.TestCase):
    def test_missing_file_returns_empty_history(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = ChatHistoryRepository(Path(directory) / "history.json")

            self.assertEqual(repository.load_all(), {})

    def test_save_and_load_preserves_sessions_and_unicode(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = ChatHistoryRepository(Path(directory) / "history.json")
            history = {
                "session_1": {
                    "title": "Bonjour",
                    "history": [{"role": "user", "parts": [{"text": "café"}]}],
                }
            }

            repository.save_all(history)

            self.assertEqual(repository.load_all(), history)
            self.assertEqual(repository.get_session("session_1"), history["session_1"])

    def test_save_session_merges_with_existing_history(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = ChatHistoryRepository(Path(directory) / "history.json")
            repository.save_session("session_1", {"title": "First"})
            repository.save_session("session_2", {"title": "Second"})

            self.assertEqual(
                repository.load_all(),
                {
                    "session_1": {"title": "First"},
                    "session_2": {"title": "Second"},
                },
            )

    def test_corrupt_file_raises_storage_error(self):
        with tempfile.TemporaryDirectory() as directory:
            history_path = Path(directory) / "history.json"
            history_path.write_text("not json", encoding="utf-8")
            repository = ChatHistoryRepository(history_path)

            with self.assertRaises(StorageError):
                repository.load_all()

    def test_non_serializable_values_raise_storage_error(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = ChatHistoryRepository(Path(directory) / "history.json")

            with self.assertRaises(StorageError):
                repository.save_all({"session": {"value": object()}})


if __name__ == "__main__":
    unittest.main()