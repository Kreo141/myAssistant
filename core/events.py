"""Named states used for communication between orchestration and UI layers."""

from enum import Enum


class AssistantState(str, Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    SCANNING = "scanning"
    STOPPING = "stopping"