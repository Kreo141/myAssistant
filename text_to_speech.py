"""Compatibility exports for the legacy text-to-speech module."""

import os

from dotenv import load_dotenv

from audio.text_to_speech import GeminiTTSProvider
from utils.audio_utils import parse_audio_mime_type, pcm_to_wav

load_dotenv()


class TextToSpeechGenerator:
    @staticmethod
    def generate(text: str) -> bytes:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY was not found in the environment")
        return GeminiTTSProvider(api_key).generate(text)

    @staticmethod
    def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
        return pcm_to_wav(audio_data, mime_type)

    @staticmethod
    def parse_audio_mime_type(mime_type: str) -> dict[str, int]:
        return parse_audio_mime_type(mime_type)


__all__ = ["GeminiTTSProvider", "TextToSpeechGenerator"]