"""Spoken confirmation handling for risky actions."""

from __future__ import annotations

from collections.abc import Callable


class ConfirmationService:
    _affirmative = {
        "yes",
        "yeah",
        "yep",
        "sure",
        "confirm",
        "confirmed",
        "go ahead",
        "do it",
    }
    _negative = {"no", "nope", "cancel", "stop", "never mind"}

    def __init__(
        self,
        speak: Callable[[str], None],
        listen: Callable[[], str | None],
    ) -> None:
        self._speak = speak
        self._listen = listen

    def confirm(self, prompt: str) -> bool:
        self._speak(prompt)
        response = self._listen()
        return self.interpret(response)

    @classmethod
    def interpret(cls, response: str | None) -> bool:
        if not response:
            return False

        normalized = " ".join(response.lower().strip().split())
        if normalized in cls._negative:
            return False
        return normalized in cls._affirmative