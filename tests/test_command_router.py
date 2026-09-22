import unittest

from core.models import ActionRequest, ActionResult
from orchestration.command_router import CommandRouter


class DummyRegistry:
    def __init__(self):
        self.calls = []

    def dispatch(self, request):
        self.calls.append(request)
        return ActionResult(success=True, message="done", data={"exit": request.name == "exit"})


class DummyGeminiClient:
    def __init__(self):
        self.calls = []

    def generate_chat(self, **kwargs):
        self.calls.append(kwargs)
        return "Gemini response"


class DummyVisionAnalyzer:
    def __init__(self):
        self.calls = []

    def analyze(self, text):
        self.calls.append(text)
        return ActionRequest(name="describe_screen", data={"response": "screen details"})


class DummyIntentClassifier:
    def classify_local(self, text):
        return "greetings"

    def classify_gemini_task(self, text):
        return "general_chat"


class CommandRouterTests(unittest.TestCase):
    def test_routes_local_actions(self):
        registry = DummyRegistry()
        router = CommandRouter(
            registry=registry,
            intent_classifier=DummyIntentClassifier(),
            gemini_client=DummyGeminiClient(),
            vision_analyzer=DummyVisionAnalyzer(),
            model="gemini-pro",
            system_instruction="prompt",
        )

        result = router.route_local_action("hello")

        self.assertTrue(result.success)
        self.assertEqual(registry.calls[0].name, "greetings")

    def test_routes_gemini_chat(self):
        router = CommandRouter(
            registry=DummyRegistry(),
            intent_classifier=DummyIntentClassifier(),
            gemini_client=DummyGeminiClient(),
            vision_analyzer=DummyVisionAnalyzer(),
            model="gemini-pro",
            system_instruction="prompt",
        )

        text = router.route_gemini_chat("hello")

        self.assertEqual(text, "Gemini response")

    def test_routes_screen_analysis(self):
        router = CommandRouter(
            registry=DummyRegistry(),
            intent_classifier=DummyIntentClassifier(),
            gemini_client=DummyGeminiClient(),
            vision_analyzer=DummyVisionAnalyzer(),
            model="gemini-pro",
            system_instruction="prompt",
        )

        request = router.route_screen_analysis("describe this")

        self.assertEqual(request.name, "describe_screen")
        self.assertEqual(request.data["response"], "screen details")


if __name__ == "__main__":
    unittest.main()
