import importlib
import unittest
from unittest.mock import patch


class AppStartupTests(unittest.TestCase):
    def test_main_starts_runtime_before_exec(self):
        with patch("main.build_runtime") as build_runtime:
            with patch("main.QApplication") as mock_qapp:
                with patch("main.FloatingWindow") as mock_window:
                    with patch("main.UIController") as mock_controller:
                        with patch("main.Thread") as mock_thread:
                            module = importlib.import_module("main")
                            module.main()

                            self.assertGreaterEqual(build_runtime.call_count, 1)
                            self.assertEqual(mock_thread.call_count, 1)
                            mock_qapp.return_value.exec_.assert_called_once()


if __name__ == "__main__":
    unittest.main()
