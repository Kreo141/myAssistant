"""OpenWakeWord model ownership and prediction handling."""

from __future__ import annotations

from typing import Any, Iterable

try:
    import openwakeword
    from openwakeword.model import Model
except Exception as exc:  # pragma: no cover - environment-specific import issue
    openwakeword = None
    Model = None
    _OPENWAKEWORD_IMPORT_ERROR = exc
else:
    _OPENWAKEWORD_IMPORT_ERROR = None


class WakeWordDetector:
    def __init__(
        self,
        wake_words: Iterable[str],
        vad_threshold: float = 0.5,
        model: Any | None = None,
        download_models: bool = True,
    ) -> None:
        if model is None:
            if Model is None or openwakeword is None:
                raise RuntimeError(
                    "OpenWakeWord is not available in this environment. "
                    "Install the wake-word dependency or provide a mocked model "
                    "when testing."
                ) from _OPENWAKEWORD_IMPORT_ERROR

            if download_models:
                openwakeword.utils.download_models()
            model = Model(
                wakeword_models=list(wake_words),
                vad_threshold=vad_threshold,
            )

        self._model = model

    def predict(self, audio_data: Any) -> dict[str, float]:
        self._model.predict(audio_data)
        scores: dict[str, float] = {}

        for wake_word, prediction_buffer in self._model.prediction_buffer.items():
            if prediction_buffer:
                scores[wake_word] = list(prediction_buffer)[-1]

        return scores

    def reset(self) -> None:
        self._model.reset()