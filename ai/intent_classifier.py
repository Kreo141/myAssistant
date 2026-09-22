"""Local intent model loading and classification."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Callable

from core.exceptions import AIServiceError


class IntentClassifier:
    def __init__(
        self,
        model_directory: Path,
        model_loader: Callable[[Any], Any] | None = None,
    ) -> None:
        self._model_directory = model_directory
        self._model_loader = model_loader or pickle.load
        self._intent_model, self._intent_vectorizer = self._load_pair(
            "intent_model_intent.pkl",
            "vectorizer_intent.pkl",
        )
        self._task_model, self._task_vectorizer = self._load_pair(
            "intent_model_genai_task_intent.pkl",
            "vectorizer_genai_task_intent.pkl",
        )

    def classify_local(self, text: str) -> str:
        return self._predict(self._intent_model, self._intent_vectorizer, text)

    def classify_gemini_task(self, text: str) -> str:
        return self._predict(self._task_model, self._task_vectorizer, text)

    def _load_pair(self, model_name: str, vectorizer_name: str) -> tuple[Any, Any]:
        try:
            with (self._model_directory / model_name).open("rb") as model_file:
                model = self._model_loader(model_file)
            with (self._model_directory / vectorizer_name).open("rb") as vectorizer_file:
                vectorizer = self._model_loader(vectorizer_file)
        except (OSError, pickle.PickleError, EOFError) as error:
            raise AIServiceError(
                f"Could not load intent model files from {self._model_directory}"
            ) from error
        return model, vectorizer

    @staticmethod
    def _predict(model: Any, vectorizer: Any, text: str) -> str:
        try:
            features = vectorizer.transform([text])
            return model.predict(features)[0]
        except Exception as error:
            raise AIServiceError("Intent classification failed") from error