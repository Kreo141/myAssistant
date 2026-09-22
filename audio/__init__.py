"""Audio input, wake-word detection, and speech services."""

from .microphone import Microphone
from .speech_to_text import SpeechToTextService
from .text_to_speech import GeminiTTSProvider, GoogleTTSProvider, TextToSpeechService

__all__ = [
	"GeminiTTSProvider",
	"GoogleTTSProvider",
	"Microphone",
	"SpeechToTextService",
	"TextToSpeechService",
]


def __getattr__(name):
    if name == "WakeWordDetector":
        from .wake_word import WakeWordDetector
        return WakeWordDetector
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")