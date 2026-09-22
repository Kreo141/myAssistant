import unittest

from actions.calendar_actions import CalendarActions
from actions.computer_actions import ComputerActions
from actions.confirmation import ConfirmationService
from actions.registry import ActionRegistry, create_default_registry
from core.exceptions import ActionError
from core.models import ActionRequest


class FakeConfirmation:
    def __init__(self, result):
        self.result = result
        self.prompts = []

    def confirm(self, prompt):
        self.prompts.append(prompt)
        return self.result


class ActionTests(unittest.TestCase):
    def test_confirmation_accepts_explicit_phrases_only(self):
        accepted = ["yes", "Sure", "go ahead", "  do   it "]
        rejected = [None, "maybe", "yes please maybe", "cancel", "no"]

        for response in accepted:
            self.assertTrue(ConfirmationService.interpret(response))
        for response in rejected:
            self.assertFalse(ConfirmationService.interpret(response))

    def test_computer_actions_are_injectable_and_safe(self):
        calls = []
        visible_titles = {10: "Notepad", 11: "Settings", 12: "Program Manager"}

        actions = ComputerActions(
            lock_workstation=lambda: calls.append("lock"),
            enumerate_windows=lambda callback, extra: [callback(hwnd, extra) for hwnd in visible_titles],
            is_window_visible=lambda hwnd: True,
            get_window_text=lambda hwnd: visible_titles[hwnd],
            post_message=lambda hwnd, message, first, second: calls.append((hwnd, message)),
        )

        actions.lock_computer()
        actions.close_all_windows()
        shutdown_result = actions.shutdown_computer()

        self.assertEqual(calls[0], "lock")
        self.assertEqual(calls[1][0], 10)
        self.assertFalse(shutdown_result.success)

    def test_calendar_actions_validate_and_forward_events(self):
        events = []
        actions = CalendarActions(create_event=events.append)
        request = ActionRequest(
            name="add_calendar",
            data={
                "title": "Meeting",
                "date": "2026-09-22",
                "start_time": "10:00",
                "end_time": "11:00",
                "description": None,
            },
        )

        result = actions.add_event(request)

        self.assertTrue(result.success)
        self.assertEqual(events, [request.data])

    def test_calendar_actions_reject_invalid_time(self):
        actions = CalendarActions()
        request = ActionRequest(
            name="add_calendar",
            data={
                "title": "Meeting",
                "date": "2026-09-22",
                "start_time": "11:00",
                "end_time": "10:00",
                "description": None,
            },
        )

        result = actions.add_event(request)

        self.assertFalse(result.success)

    def test_registry_dispatches_and_rejects_unknown_actions(self):
        registry = ActionRegistry()
        registry.register("test", lambda request: type("Result", (), {"success": True})())

        self.assertTrue(registry.dispatch(ActionRequest("test")).success)
        with self.assertRaises(ActionError):
            registry.dispatch(ActionRequest("missing"))

    def test_default_registry_requires_confirmation_for_exit(self):
        spoken = []
        exited = []
        confirmation = FakeConfirmation(False)
        registry = create_default_registry(
            computer_actions=ComputerActions(
                lock_workstation=lambda: None,
                enumerate_windows=lambda callback, extra: None,
                is_window_visible=lambda hwnd: False,
                get_window_text=lambda hwnd: "",
                post_message=lambda *args: None,
            ),
            calendar_actions=CalendarActions(),
            confirmation_service=confirmation,
            speak=spoken.append,
            on_exit=lambda: exited.append(True),
        )

        result = registry.dispatch(ActionRequest("exit"))

        self.assertFalse(result.success)
        self.assertEqual(exited, [])
        self.assertEqual(confirmation.prompts, ["Are you sure you want to exit?"])


if __name__ == "__main__":
    unittest.main()