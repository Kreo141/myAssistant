import unittest

from ui.ui_controller import UIController


class FakeWindow:
    def __init__(self):
        self.visible = False
        self.response = ""
        self.wave_count = 0
        self.scan_state = None

    def set_response(self, response):
        self.response = response

    def set_visible(self, visible):
        self.visible = visible

    def trigger_wave(self):
        self.wave_count += 1

    def trigger_scan(self, enabled):
        self.scan_state = bool(enabled)


class UiControllerTests(unittest.TestCase):
    def test_controller_delegates_to_the_window(self):
        fake_window = FakeWindow()
        controller = UIController(fake_window)

        controller.set_response("hello")
        controller.show_wake_indicator()
        controller.show_scan(True)
        controller.hide()

        self.assertEqual(fake_window.response, "hello")
        self.assertEqual(fake_window.wave_count, 1)
        self.assertTrue(fake_window.scan_state)
        self.assertFalse(fake_window.visible)


if __name__ == "__main__":
    unittest.main()
