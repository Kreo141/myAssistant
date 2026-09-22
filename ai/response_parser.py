"""Validation for structured Gemini action responses."""

from __future__ import annotations

import json
from typing import Any

from core.exceptions import AIServiceError
from core.models import ActionRequest


class ResponseParser:
    _allowed_fields = {
        "none": set(),
        "describe_screen": {"response"},
        "add_calendar": {
            "title",
            "date",
            "start_time",
            "end_time",
            "description",
        },
    }

    def parse_action(self, response_text: str) -> ActionRequest:
        try:
            response = json.loads(response_text)
        except json.JSONDecodeError as error:
            raise AIServiceError("Gemini returned invalid JSON") from error

        if not isinstance(response, dict):
            raise AIServiceError("Gemini action response must be a JSON object")

        action = response.get("action")
        data = response.get("data")
        if action not in self._allowed_fields:
            raise AIServiceError(f"Gemini returned an unknown action: {action}")
        if not isinstance(data, dict):
            raise AIServiceError("Gemini action data must be a JSON object")

        unexpected_fields = set(data) - self._allowed_fields[action]
        if unexpected_fields:
            raise AIServiceError(
                f"Gemini action contains unexpected fields: {sorted(unexpected_fields)}"
            )

        if action == "describe_screen" and not isinstance(data.get("response"), str):
            raise AIServiceError("describe_screen requires a string response")

        if action == "add_calendar" and set(data) != self._allowed_fields[action]:
            raise AIServiceError("add_calendar requires all defined event fields")

        return ActionRequest(name=action, data=data)