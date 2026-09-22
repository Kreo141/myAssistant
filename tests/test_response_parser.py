import unittest

from ai.response_parser import ResponseParser
from core.exceptions import AIServiceError


class ResponseParserTests(unittest.TestCase):
    def setUp(self):
        self.parser = ResponseParser()

    def test_parses_describe_screen_action(self):
        action = self.parser.parse_action(
            '{"action":"describe_screen","data":{"response":"A browser is open."}}'
        )

        self.assertEqual(action.name, "describe_screen")
        self.assertEqual(action.data["response"], "A browser is open.")

    def test_rejects_invalid_json(self):
        with self.assertRaises(AIServiceError):
            self.parser.parse_action("not json")

    def test_rejects_unknown_action(self):
        with self.assertRaises(AIServiceError):
            self.parser.parse_action('{"action":"unknown","data":{}}')

    def test_rejects_unexpected_fields(self):
        with self.assertRaises(AIServiceError):
            self.parser.parse_action(
                '{"action":"none","data":{"response":"unexpected"}}'
            )

    def test_rejects_missing_describe_screen_response(self):
        with self.assertRaises(AIServiceError):
            self.parser.parse_action('{"action":"describe_screen","data":{}}')

    def test_rejects_incomplete_calendar_data(self):
        with self.assertRaises(AIServiceError):
            self.parser.parse_action(
                '{"action":"add_calendar","data":{"title":"Meeting"}}'
            )


if __name__ == "__main__":
    unittest.main()