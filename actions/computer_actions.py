"""Windows computer actions behind an injectable boundary."""

from __future__ import annotations

import ctypes
import os
from collections.abc import Callable
from typing import Any

import win32con
import win32gui

from core.models import ActionResult


class ComputerActions:
    def __init__(
        self,
        lock_workstation: Callable[[], Any] | None = None,
        enumerate_windows: Callable[[Callable[..., Any], Any], Any] | None = None,
        is_window_visible: Callable[[int], bool] | None = None,
        get_window_text: Callable[[int], str] | None = None,
        post_message: Callable[[int, int, int, int], Any] | None = None,
        shutdown_command: Callable[[], Any] | None = None,
    ) -> None:
        self._lock_workstation = lock_workstation or ctypes.windll.user32.LockWorkStation
        self._enumerate_windows = enumerate_windows or win32gui.EnumWindows
        self._is_window_visible = is_window_visible or win32gui.IsWindowVisible
        self._get_window_text = get_window_text or win32gui.GetWindowText
        self._post_message = post_message or win32gui.PostMessage
        self._shutdown_command = shutdown_command

    def lock_computer(self) -> ActionResult:
        self._lock_workstation()
        return ActionResult(success=True, message="Computer locked.")

    def close_all_windows(self) -> ActionResult:
        self._enumerate_windows(self._close_window, None)
        return ActionResult(success=True, message="Windows closed.")

    def shutdown_computer(self) -> ActionResult:
        if self._shutdown_command is None:
            return ActionResult(
                success=False,
                message="Shutdown is currently disabled.",
            )

        self._shutdown_command()
        return ActionResult(success=True, message="Computer shutting down.")

    def _close_window(self, hwnd: int, extra: Any) -> None:
        if not self._is_window_visible(hwnd):
            return

        title = self._get_window_text(hwnd)
        if title and title not in {"Program Manager", "Settings"}:
            self._post_message(hwnd, win32con.WM_CLOSE, 0, 0)


def windows_shutdown_command() -> None:
    os.system("shutdown /s /t 1")