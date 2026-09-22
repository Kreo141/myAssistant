"""Coordinator for wake-word detection, audio capture, classification, and routing."""

from __future__ import annotations

from threading import Event
from typing import Any, Callable

import numpy as np

from core.events import AssistantState


class Assistant:
    def __init__(
        self,
        wake_detector: Any,
        microphone: Any,
        speech_to_text_service: Any,
        router: Any,
        tts_service: Any,
        ui_controller: Any,
        max_command_seconds: float = 5.0,
        speech_energy_threshold: float = 500,
        silence_after_seconds: float = 1.0,
        sample_rate: int = 16000,
        pcm_converter: Callable[[Any, int, int], Any] | None = None,
        stop_event: Event | None = None,
    ) -> None:
        self.wake_detector = wake_detector
        self.microphone = microphone
        self.speech_to_text_service = speech_to_text_service
        self.router = router
        self.tts_service = tts_service
        self.ui_controller = ui_controller
        self.max_command_seconds = max_command_seconds
        self.speech_energy_threshold = speech_energy_threshold
        self.silence_after_seconds = silence_after_seconds
        self.sample_rate = sample_rate
        self.pcm_converter = pcm_converter
        self.stop_event = stop_event or Event()
        self.state = AssistantState.IDLE

    def run_loop(self) -> None:
        while not self.stop_event.is_set():
            data = self.microphone.read_chunk()
            audio_data = np.frombuffer(data, dtype=np.int16)
            wake_scores = self.wake_detector.predict(audio_data)

            for wake_word, score in wake_scores.items():
                if score <= 0.5:
                    continue

                self.state = AssistantState.LISTENING
                self._announce_wake(wake_word)
                command = self._capture_command()
                if not command:
                    self.wake_detector.reset()
                    break

                response = self._process_command(command, wake_word)
                if response is not None and hasattr(response, "data") and response.data.get("exit"):
                    return

                self.wake_detector.reset()
                break

    def _announce_wake(self, wake_word: str) -> None:
        if self.ui_controller is not None:
            self.ui_controller.show_wake_indicator()
        if wake_word == "hey_jarvis":
            self.tts_service.speak("Hey!")
        else:
            self.tts_service.speak("What's up?")
        if self.ui_controller is not None:
            self.ui_controller.hide()

    def _capture_command(self) -> str:
        self.state = AssistantState.LISTENING
        raw_audio = self.microphone.record_command(
            max_seconds=self.max_command_seconds,
            energy_threshold=self.speech_energy_threshold,
            silence_after_seconds=self.silence_after_seconds,
        )
        if self.pcm_converter is not None:
            audio_data = self.pcm_converter(raw_audio, self.sample_rate, 2)
        else:
            audio_data = raw_audio
        return self.speech_to_text_service.transcribe(audio_data)

    def _process_command(self, command: str, wake_word: str):
        if wake_word == "hey_jarvis":
            intent = self.router.intent_classifier.classify_gemini_task(command)
            if intent == "general_chat":
                self.state = AssistantState.THINKING
                if self.ui_controller is not None:
                    self.ui_controller.show()
                reply = self.router.route_gemini_chat(command)
                self.tts_service.speak(reply)
                if self.ui_controller is not None:
                    self.ui_controller.hide()
                return None
            if intent == "analyze_screen":
                self.state = AssistantState.SCANNING
                if self.ui_controller is not None:
                    self.ui_controller.show_scan(True)
                request = self.router.route_screen_analysis(command)
                if request.name == "describe_screen":
                    response_text = request.data.get("response")
                    if response_text:
                        self.tts_service.speak(response_text)
                if self.ui_controller is not None:
                    self.ui_controller.show_scan(False)
                return None

        result = self.router.route_local_action(command)
        if result.data.get("exit"):
            self.state = AssistantState.STOPPING
            return result
        return result
