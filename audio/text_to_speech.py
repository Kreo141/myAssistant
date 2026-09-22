"""Text-to-speech providers and audio playback."""

from __future__ import annotations

import io
from collections.abc import Callable
from typing import Any

import pygame
from gtts import gTTS

from ai.gemini_client import GeminiClient
from core.exceptions import AudioError
from utils.audio_utils import pcm_to_wav


class GeminiTTSProvider:
    def __init__(
        self,
        api_key: str,
        client: Any | None = None,
        model: str = "gemini-3.1-flash-tts-preview",
        voice_name: str = "Iapetus",
    ) -> None:
        self._client = client or GeminiClient(api_key=api_key)
        self._model = model
        self._voice_name = voice_name

    def generate(self, text: str) -> bytes:
        try:
            audio_data, mime_type = self._client.generate_tts(
                text=text,
                model=self._model,
                voice_name=self._voice_name,
            )
            return pcm_to_wav(audio_data, mime_type)
        except Exception as error:
            if isinstance(error, AudioError):
                raise
            raise AudioError("Gemini TTS generation failed") from error


class GoogleTTSProvider:
    def __init__(self, language: str = "en") -> None:
        self._language = language

    def generate(self, text: str) -> bytes:
        audio_stream = io.BytesIO()
        gTTS(text=text, lang=self._language).write_to_fp(audio_stream)
        return audio_stream.getvalue()


class TextToSpeechService:
    def __init__(
        self,
        use_gemini: bool,
        gemini_api_key: str | None = None,
        gemini_provider: Any | None = None,
        google_provider: Any | None = None,
        mixer: Any | None = None,
        wait_function: Callable[[int], None] | None = None,
        response_callback: Callable[[str], None] | None = None,
    ) -> None:
        self._use_gemini = use_gemini
        self._gemini_provider = gemini_provider
        if use_gemini and self._gemini_provider is None:
            if not gemini_api_key:
                raise AudioError("Gemini TTS requires a Gemini API key")
            self._gemini_provider = GeminiTTSProvider(gemini_api_key)

        self._google_provider = google_provider or GoogleTTSProvider()
        self._mixer = mixer or pygame.mixer
        self._wait = wait_function or pygame.time.wait
        self._response_callback = response_callback

    def speak(self, text: str) -> None:
        if self._response_callback is not None:
            self._response_callback(text)

        audio_data = self._generate_audio(text)
        if not audio_data:
            raise AudioError("Text-to-speech returned no audio data")

        audio_stream = io.BytesIO(audio_data)
        try:
            self._mixer.init()
            self._mixer.music.load(audio_stream)
            self._mixer.music.play()

            while self._mixer.music.get_busy():
                self._wait(100)
        except Exception as error:
            raise AudioError("Could not play text-to-speech audio") from error
        finally:
            self._mixer.quit()

    def close(self) -> None:
        self._mixer.quit()

    def _generate_audio(self, text: str) -> bytes:
        if not self._use_gemini:
            return self._google_provider.generate(text)

        try:
            return self._gemini_provider.generate(text)
        except Exception as error:
            print(f"[ERROR] Gemini TTS failed, using Google TTS: {error}")
            return self._google_provider.generate(text)