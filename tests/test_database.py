import tempfile
import unittest
from pathlib import Path

from storage.database import Database


class DatabaseTests(unittest.TestCase):
    def test_initialize_schema_creates_conversation_tables(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "assistant.db")

            database.initialize_schema()

            with database.transaction() as connection:
                tables = connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type = 'table' ORDER BY name"
                ).fetchall()

            self.assertEqual(
                [row[0] for row in tables],
                ["conversations", "messages", "sqlite_sequence"],
            )

    def test_transaction_rolls_back_on_error(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "assistant.db")
            database.initialize_schema()

            with self.assertRaises(RuntimeError):
                with database.transaction() as connection:
                    connection.execute(
                        "INSERT INTO conversations (id, title) VALUES (?, ?)",
                        ("session_1", "Test"),
                    )
                    raise RuntimeError("abort")

            with database.transaction() as connection:
                count = connection.execute(
                    "SELECT COUNT(*) FROM conversations"
                ).fetchone()[0]

            self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()