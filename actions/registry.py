"""Action registration and default assistant action handlers."""

from __future__ import annotations

from collections.abc import Callable

from core.exceptions import ActionError
from core.models import ActionRequest, ActionResult

from .calendar_actions import CalendarActions
from .computer_actions import ComputerActions
from .confirmation import ConfirmationService


ActionHandler = Callable[[ActionRequest], ActionResult]


class ActionRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, ActionHandler] = {}

    def register(self, action_name: str, handler: ActionHandler) -> None:
        if not action_name:
            raise ActionError("Action name cannot be empty")
        self._handlers[action_name] = handler

    def dispatch(self, request: ActionRequest) -> ActionResult:
        handler = self._handlers.get(request.name)
        if handler is None:
            raise ActionError(f"No handler registered for action: {request.name}")
        return handler(request)


def create_default_registry(
    computer_actions: ComputerActions,
    calendar_actions: CalendarActions,
    confirmation_service: ConfirmationService,
    speak: Callable[[str], None],
    on_exit: Callable[[], None],
) -> ActionRegistry:
    registry = ActionRegistry()

    registry.register(
        "greetings",
        lambda request: _speak_success(speak, "Hello! How can I assist you?"),
    )
    registry.register(
        "lock_computer",
        lambda request: _run_with_speech(
            speak,
            "Locking the computer...",
            computer_actions.lock_computer,
        ),
    )
    registry.register(
        "close_all_windows",
        lambda request: computer_actions.close_all_windows(),
    )
    registry.register(
        "shutdown_computer",
        lambda request: _confirm_and_run(
            confirmation_service,
            speak,
            "Are you sure you want to do this?",
            "Shutting down...",
            computer_actions.shutdown_computer,
        ),
    )
    registry.register(
        "exit",
        lambda request: _confirm_and_exit(
            confirmation_service,
            speak,
            "Are you sure you want to exit?",
            on_exit,
        ),
    )
    registry.register("add_calendar", calendar_actions.add_event)
    return registry


def _speak_success(speak: Callable[[str], None], message: str) -> ActionResult:
    speak(message)
    return ActionResult(success=True, message=message)


def _run_with_speech(
    speak: Callable[[str], None],
    announcement: str,
    action: Callable[[], ActionResult],
) -> ActionResult:
    speak(announcement)
    return action()


def _confirm_and_run(
    confirmation_service: ConfirmationService,
    speak: Callable[[str], None],
    prompt: str,
    announcement: str,
    action: Callable[[], ActionResult],
) -> ActionResult:
    if not confirmation_service.confirm(prompt):
        return ActionResult(success=False, message="Action cancelled.")
    speak(announcement)
    return action()


def _confirm_and_exit(
    confirmation_service: ConfirmationService,
    speak: Callable[[str], None],
    prompt: str,
    on_exit: Callable[[], None],
) -> ActionResult:
    if not confirmation_service.confirm(prompt):
        speak("Okay!")
        return ActionResult(success=False, message="Exit cancelled.")
    speak("Exiting...")
    on_exit()
    return ActionResult(success=True, message="Exiting...", data={"exit": True})