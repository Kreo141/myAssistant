"""Calendar action validation and integration boundary."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from core.models import ActionRequest, ActionResult


class CalendarActions:
    _required_fields = {
        "title",
        "date",
        "start_time",
        "end_time",
        "description",
    }

    def __init__(self, create_event: Callable[[dict[str, Any]], Any] | None = None) -> None:
        self._create_event = create_event

    def add_event(self, request: ActionRequest) -> ActionResult:
        data = request.data
        if set(data) != self._required_fields:
            return ActionResult(
                success=False,
                message="Calendar event data is incomplete.",
            )

        validation_error = self._validate(data)
        if validation_error is not None:
            return ActionResult(success=False, message=validation_error)

        if self._create_event is None:
            return ActionResult(
                success=False,
                message="Calendar integration is not configured.",
                data=data,
            )

        self._create_event(data)
        return ActionResult(success=True, message="Calendar event added.", data=data)

    @staticmethod
    def _validate(data: dict[str, Any]) -> str | None:
        if not isinstance(data["title"], str) or not data["title"].strip():
            return "Calendar event title is required."

        try:
            event_date = datetime.strptime(data["date"], "%Y-%m-%d")
            start_time = datetime.strptime(data["start_time"], "%H:%M")
        except (TypeError, ValueError):
            return "Calendar date or start time is invalid."

        end_time_value = data["end_time"]
        if end_time_value is not None:
            try:
                end_time = datetime.strptime(end_time_value, "%H:%M")
            except (TypeError, ValueError):
                return "Calendar end time is invalid."
            if end_time < start_time:
                return "Calendar end time must not be before start time."

        if data["description"] is not None and not isinstance(data["description"], str):
            return "Calendar description must be text or null."

        if event_date is None:
            return "Calendar date is invalid."
        return None