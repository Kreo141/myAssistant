"""OpenWakeWord model ownership and prediction handling."""

from __future__ import annotations

from typing import Any, Iterable

import numpy as np


def _load_openwakeword():
    try:
        import importlib

        module = importlib.import_module("openwakeword")
        model_module = importlib.import_module("openwakeword.model")
        return module, model_module.Model
    except Exception as exc:  # pragma: no cover - environment-specific import issue
        return None, None, exc


class _FallbackWakeWordModel:
    def __init__(self, wake_words: Iterable[str]) -> None:
        self.wake_words = list(wake_words)
        self.prediction_buffer = {wake_word: [0.0] for wake_word in self.wake_words}

    def predict(self, audio_data: Any) -> None:
        samples = np.frombuffer(audio_data, dtype=np.int16)
        if samples.size == 0:
            scores = {wake_word: 0.0 for wake_word in self.wake_words}
        else:
            energy = float(np.mean(np.abs(samples.astype(np.float32))))
            scores = {
                wake_word: (1.0 if energy > 1000 else 0.0)
                for wake_word in self.wake_words
            }

        self.prediction_buffer = {
            wake_word: [score]
            for wake_word, score in scores.items()
        }

    def reset(self) -> None:
        self.prediction_buffer = {wake_word: [0.0] for wake_word in self.wake_words}


class WakeWordDetector:
    def __init__(
        self,
        wake_words: Iterable[str],
        vad_threshold: float = 0.5,
        model: Any | None = None,
        download_models: bool = True,
        use_native: bool = False,
    ) -> None:
        if model is not None:
            self._model = model
            return

        if not use_native:
            self._model = _FallbackWakeWordModel(wake_words)
            return

        try:
            openwakeword, Model = _load_openwakeword()
            if Model is None or openwakeword is None:
                raise RuntimeError("OpenWakeWord is unavailable")

            if download_models:
                openwakeword.utils.download_models()
            self._model = Model(
                wakeword_models=list(wake_words),
                vad_threshold=vad_threshold,
            )
        except Exception:
            print(
                "[WARNING] OpenWakeWord failed to initialize; using a safe fallback detector."
            )
            self._model = _FallbackWakeWordModel(wake_words)

    def predict(self, audio_data: Any) -> dict[str, float]:
        self._model.predict(audio_data)
        scores: dict[str, float] = {}

        for wake_word, prediction_buffer in self._model.prediction_buffer.items():
            if prediction_buffer:
                scores[wake_word] = list(prediction_buffer)[-1]

        return scores

    def reset(self) -> None:
        self._model.reset()