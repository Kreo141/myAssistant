import pickle
import tempfile
import unittest
from pathlib import Path

from ai.intent_classifier import IntentClassifier


class FakeVectorizer:
    def transform(self, values):
        return values


class FakeModel:
    def __init__(self, label):
        self.label = label

    def predict(self, values):
        return [self.label]


class IntentClassifierTests(unittest.TestCase):
    def test_loads_both_model_pairs_and_classifies(self):
        with tempfile.TemporaryDirectory() as directory:
            model_directory = Path(directory)
            objects = {
                "intent_model_intent.pkl": FakeModel("greetings"),
                "vectorizer_intent.pkl": FakeVectorizer(),
                "intent_model_genai_task_intent.pkl": FakeModel("general_chat"),
                "vectorizer_genai_task_intent.pkl": FakeVectorizer(),
            }
            for filename, value in objects.items():
                with (model_directory / filename).open("wb") as model_file:
                    pickle.dump(value, model_file)

            classifier = IntentClassifier(model_directory)

            self.assertEqual(classifier.classify_local("hello"), "greetings")
            self.assertEqual(
                classifier.classify_gemini_task("tell me something"),
                "general_chat",
            )


if __name__ == "__main__":
    unittest.main()