"""Deprecated compatibility wrapper for the extracted overlay widget."""

import warnings

from ui.floating_window import FloatingWindow

warnings.warn(
    "myGUI.py is deprecated; import FloatingWindow from ui.floating_window instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = ["FloatingWindow"]
