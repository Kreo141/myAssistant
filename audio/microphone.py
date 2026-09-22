"""Microphone ownership and speech-segment recording."""

from __future__ import annotations

from typing import Any

import numpy as np
import pyaudio

from core.exceptions import AudioError
from utils.audio_utils import calculate_rms_energy


class Microphone:
    def __init__(
        self,
        chunk_size: int = 1024,
        audio_format: int = pyaudio.paInt16,
        channels: int = 1,
        sample_rate: int = 16000,
        audio: Any | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.audio_format = audio_format
        self.channels = channels
        self.sample_rate = sample_rate
        self._audio = audio or pyaudio.PyAudio()
        self._owns_audio = audio is None
        self._stream = None

        try:
            self._stream = self._audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
            )
        except Exception as error:
            if self._owns_audio:
                self._audio.terminate()
            raise AudioError("Could not open the microphone stream") from error

    @property
    def stream(self) -> Any:
        return self._stream

    def read_chunk(self) -> bytes:
        if self._stream is None:
            raise AudioError("The microphone stream is not available")

        try:
            return self._stream.read(
                self.chunk_size,
                exception_on_overflow=False,
            )
        except Exception as error:
            raise AudioError("Could not read from the microphone") from error

    def record_command(
        self,
        max_seconds: float = 5.0,
        energy_threshold: float = 500.0,
        silence_after_seconds: float = 1.0,
    ) -> bytes:
        frames: list[bytes] = []
        speech_started = False
        silence_duration = 0.0
        chunk_duration = self.chunk_size / self.sample_rate
        chunk_count = int(max_seconds / chunk_duration)

        for _ in range(chunk_count):
            data = self.read_chunk()
            frames.append(data)
            energy = calculate_rms_energy(data)

            if energy >= energy_threshold:
                speech_started = True
                silence_duration = 0.0
            elif speech_started:
                silence_duration += chunk_duration
                if silence_duration >= silence_after_seconds:
                    break

        return b"".join(frames)

    def close(self) -> None:
        if self._stream is not None:
            try:
                if self._stream.is_active():
                    self._stream.stop_stream()
            finally:
                self._stream.close()
                self._stream = None

        if self._owns_audio:
            self._audio.terminate()