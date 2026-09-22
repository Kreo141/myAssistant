import unittest

from ai.vision_analyzer import VisionAnalyzer
from core.exceptions import AIServiceError
from ai.response_parser import ResponseParser


class FakeScreenshot:
    def save(self, image_buffer, format):
        image_buffer.write(b"jpeg-image")


class FakeGeminiClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def generate_vision(self, **kwargs):
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class VisionAnalyzerTests(unittest.TestCase):
    def test_analyze_uses_jpeg_and_clears_scan_state(self):
        client = FakeGeminiClient(
            response='{"action":"describe_screen","data":{"response":"A screen"}}'
        )
        scan_states = []
        analyzer = VisionAnalyzer(
            gemini_client=client,
            response_parser=ResponseParser(),
            model="test-model",
            system_instruction="test instruction",
            screenshot_provider=lambda: FakeScreenshot(),
            scan_callback=scan_states.append,
        )

        action = analyzer.analyze("describe this")

        self.assertEqual(action.name, "describe_screen")
        self.assertEqual(client.calls[0]["image_mime_type"], "image/jpeg")
        self.assertEqual(scan_states, [True, False])

    def test_analyze_clears_scan_state_when_gemini_fails(self):
        client = FakeGeminiClient(error=AIServiceError("request failed"))
        scan_states = []
        analyzer = VisionAnalyzer(
            gemini_client=client,
            response_parser=ResponseParser(),
            model="test-model",
            system_instruction="test instruction",
            screenshot_provider=lambda: FakeScreenshot(),
            scan_callback=scan_states.append,
        )

        with self.assertRaises(AIServiceError):
            analyzer.analyze("describe this")

        self.assertEqual(scan_states, [True, False])


if __name__ == "__main__":
    unittest.main()