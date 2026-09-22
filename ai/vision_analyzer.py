"""Screenshot capture and structured vision analysis."""

from __future__ import annotations

import io
from collections.abc import Callable
from typing import Any

import pyautogui

from ai.response_parser import ResponseParser
from core.models import ActionRequest


class VisionAnalyzer:
    def __init__(
        self,
        gemini_client: Any,
        response_parser: ResponseParser,
        model: str,
        system_instruction: str,
        screenshot_provider: Callable[[], Any] | None = None,
        scan_callback: Callable[[bool], None] | None = None,
    ) -> None:
        self._gemini_client = gemini_client
        self._response_parser = response_parser
        self._model = model
        self._system_instruction = system_instruction
        self._screenshot_provider = screenshot_provider or pyautogui.screenshot
        self._scan_callback = scan_callback

    def analyze(self, prompt: str) -> ActionRequest:
        if self._scan_callback is not None:
            self._scan_callback(True)

        try:
            screenshot = self._screenshot_provider()
            image_buffer = io.BytesIO()
            screenshot.save(image_buffer, format="JPEG")
            response_text = self._gemini_client.generate_vision(
                model=self._model,
                image_bytes=image_buffer.getvalue(),
                image_mime_type="image/jpeg",
                prompt=prompt,
                system_instruction=self._system_instruction,
            )
            return self._response_parser.parse_action(response_text)
        finally:
            if self._scan_callback is not None:
                self._scan_callback(False)