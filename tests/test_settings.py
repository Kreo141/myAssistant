import tempfile
import unittest
from pathlib import Path

from config.settings import Settings
from core.exceptions import ConfigurationError
from utils.paths import ProjectPaths


class SettingsTests(unittest.TestCase):
    def test_loads_main_section(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config.ini").write_text(
                "[Main]\n"
                "wakephrase = test_phrase\n"
                "sensitivity = 0.7\n"
                "general_system_prompt = General\n"
                "vision_system_prompt = Vision\n"
                "gemini_model = test-model\n"
                "gemini_tts = true\n",
                encoding="utf-8",
            )

            settings = Settings.load(ProjectPaths(root))

            self.assertEqual(settings.wake_phrase, "test_phrase")
            self.assertEqual(settings.sensitivity, 0.7)
            self.assertTrue(settings.gemini_tts)
            self.assertEqual(settings.gemini_model, "test-model")

    def test_missing_configuration_raises_configuration_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ConfigurationError):
                Settings.load(ProjectPaths(Path(directory)))


if __name__ == "__main__":
    unittest.main()