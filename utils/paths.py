"""Project-relative filesystem paths."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path

    @classmethod
    def discover(cls) -> "ProjectPaths":
        return cls(Path(__file__).resolve().parents[1])

    @property
    def config_file(self) -> Path:
        return self.root / "config.ini"

    @property
    def env_file(self) -> Path:
        return self.root / ".env"

    @property
    def intent_model_dir(self) -> Path:
        return self.root / "intentClassificationModel" / "models"

    @property
    def chat_history_file(self) -> Path:
        return self.root / "chat_history.json"

    @property
    def database_file(self) -> Path:
        return self.root / "assistant.db"

    @property
    def credentials_file(self) -> Path:
        return self.root / "credentials.json"