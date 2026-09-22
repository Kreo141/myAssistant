"""Deprecated compatibility wrapper for the old top-level TTS module."""

import warnings

from audio.text_to_speech import GeminiTTSProvider
from utils.audio_utils import parse_audio_mime_type, pcm_to_wav

warnings.warn(
    "text_to_speech.py is deprecated; use audio.text_to_speech instead.",
    DeprecationWarning,
    stacklevel=2,
)

TextToSpeechGenerator = None

__all__ = ["GeminiTTSProvider", "TextToSpeechGenerator", "parse_audio_mime_type", "pcm_to_wav"]