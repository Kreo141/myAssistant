"""Assistant action handlers and dispatch."""

from .calendar_actions import CalendarActions
from .computer_actions import ComputerActions
from .confirmation import ConfirmationService
from .registry import ActionRegistry, create_default_registry

__all__ = [
    "ActionRegistry",
    "CalendarActions",
    "ComputerActions",
    "ConfirmationService",
    "create_default_registry",
]