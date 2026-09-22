"""Data contracts shared by application layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class VoiceCommand:
    text: str
    wake_phrase: str


@dataclass(frozen=True)
class IntentResult:
    name: str
    command: VoiceCommand
    confidence: float | None = None
    source: str = "local"


@dataclass(frozen=True)
class ActionRequest:
    name: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionResult:
    success: bool
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AssistantResponse:
    text: str
    action: ActionRequest | None = None