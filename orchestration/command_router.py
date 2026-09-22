"""Routes recognized commands to the appropriate action or AI path."""

from __future__ import annotations

from typing import Any

from actions.registry import ActionRegistry
from ai.intent_classifier import IntentClassifier
from ai.vision_analyzer import VisionAnalyzer
from core.exceptions import ActionError, AIServiceError
from core.models import ActionRequest, ActionResult


class CommandRouter:
    def __init__(
        self,
        registry: ActionRegistry,
        intent_classifier: IntentClassifier,
        gemini_client: Any,
        vision_analyzer: VisionAnalyzer,
        model: str,
        system_instruction: str,
    ) -> None:
        self.registry = registry
        self.intent_classifier = intent_classifier
        self.gemini_client = gemini_client
        self.vision_analyzer = vision_analyzer
        self.model = model
        self.system_instruction = system_instruction

    def route_local_action(self, text: str) -> ActionResult:
        intent = self.intent_classifier.classify_local(text)
        request = ActionRequest(name=intent)
        return self.registry.dispatch(request)

    def route_gemini_chat(self, text: str) -> str:
        return self.gemini_client.generate_chat(
            model=self.model,
            prompt=text,
            system_instruction=self.system_instruction,
        )

    def route_screen_analysis(self, text: str) -> ActionRequest:
        request = self.vision_analyzer.analyze(text)
        if request is None:
            raise AIServiceError("Vision analyzer returned no request")
        return request

    def route_action(self, text: str, is_gemini_task: bool = False) -> Any:
        if is_gemini_task:
            return self.route_gemini_chat(text)
        return self.route_local_action(text)

    def route_intent(self, text: str, wake_mode: str) -> Any:
        if wake_mode == "jarvis":
            intent = self.intent_classifier.classify_gemini_task(text)
            if intent == "general_chat":
                return self.route_gemini_chat(text)
            if intent == "analyze_screen":
                return self.route_screen_analysis(text)
            raise ActionError(f"Unsupported Gemini intent: {intent}")

        return self.route_local_action(text)
