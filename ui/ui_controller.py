"""Thin controller that keeps UI state changes behind a service boundary."""

from __future__ import annotations

from typing import Optional

from ui.floating_window import FloatingWindow


class UIController:
    """Coordinate overlay visibility and animated helper states for the runtime."""

    def __init__(self, window: Optional[FloatingWindow] = None):
        self.window = window or FloatingWindow()

    def set_response(self, response: str) -> None:
        if self.window is not None:
            self.window.set_response(response)

    def show(self) -> None:
        if self.window is not None:
            self.window.set_visible(True)

    def hide(self) -> None:
        if self.window is not None:
            self.window.set_visible(False)

    def show_wake_indicator(self) -> None:
        if self.window is not None:
            self.window.trigger_wave()
            self.window.set_visible(True)

    def show_scan(self, enabled: bool) -> None:
        if self.window is not None:
            self.window.trigger_scan(enabled)
            if enabled:
                self.window.set_visible(True)

    def destroy(self) -> None:
        if self.window is not None:
            self.window.close()
