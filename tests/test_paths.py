import unittest
from pathlib import Path

from utils.paths import ProjectPaths


class ProjectPathsTests(unittest.TestCase):
    def test_paths_are_relative_to_project_root(self):
        paths = ProjectPaths(Path("C:/assistant"))

        self.assertEqual(paths.config_file, Path("C:/assistant/config.ini"))
        self.assertEqual(paths.env_file, Path("C:/assistant/.env"))
        self.assertEqual(
            paths.intent_model_dir,
            Path("C:/assistant/intentClassificationModel/models"),
        )


if __name__ == "__main__":
    unittest.main()