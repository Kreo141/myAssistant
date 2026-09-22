"""Speech recognition service."""

from __future__ import annotations

from typing import Any

import speech_recognition as sr


class SpeechToTextService:
    def __init__(self, recognizer: Any | None = None) -> None:
        self._recognizer = recognizer or sr.Recognizer()

    def transcribe(self, audio_data: sr.AudioData) -> str | None:
        try:
            text = self._recognizer.recognize_google(audio_data)
            print(f"You said: {text}")
            return text
        except sr.UnknownValueError:
            print("Could not understand the audio.")
        except sr.RequestError as error:
            print(f"Google Speech Recognition error: {error}")

        return None