"""Repository for the existing chat_history.json format."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from core.exceptions import StorageError


class ChatHistoryRepository:
    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path

    def load_all(self) -> dict[str, Any]:
        if not self._file_path.exists():
            return {}

        try:
            with self._file_path.open("r", encoding="utf-8") as history_file:
                history = json.load(history_file)
        except (OSError, json.JSONDecodeError) as error:
            raise StorageError(
                f"Could not read chat history: {self._file_path}"
            ) from error

        if not isinstance(history, dict):
            raise StorageError("Chat history must contain a JSON object")
        return history

    def save_all(self, history: Mapping[str, Any]) -> None:
        if not isinstance(history, Mapping):
            raise StorageError("Chat history must be a mapping")

        try:
            serialized = json.dumps(history, indent=4, ensure_ascii=False)
        except (TypeError, ValueError) as error:
            raise StorageError("Chat history contains values that cannot be serialized") from error

        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self._file_path.with_name(
            f".{self._file_path.name}.tmp"
        )
        try:
            temporary_path.write_text(serialized + "\n", encoding="utf-8")
            os.replace(temporary_path, self._file_path)
        except OSError as error:
            if temporary_path.exists():
                temporary_path.unlink()
            raise StorageError(
                f"Could not write chat history: {self._file_path}"
            ) from error

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        session = self.load_all().get(session_id)
        if session is None:
            return None
        if not isinstance(session, dict):
            raise StorageError(f"Session is not a JSON object: {session_id}")
        return session

    def save_session(self, session_id: str, session: Mapping[str, Any]) -> None:
        if not session_id:
            raise StorageError("Session ID cannot be empty")
        if not isinstance(session, Mapping):
            raise StorageError("Session must be a mapping")

        history = self.load_all()
        history[session_id] = dict(session)
        self.save_all(history)