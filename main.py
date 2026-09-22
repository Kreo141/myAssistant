import numpy as np
import sys
from threading import Event, Thread
from PyQt5.QtWidgets import QApplication
from ui.floating_window import FloatingWindow
from ui.ui_controller import UIController
from actions.calendar_actions import CalendarActions
from actions.computer_actions import ComputerActions
from actions.confirmation import ConfirmationService
from actions.registry import create_default_registry
from ai.gemini_client import GeminiClient
from ai.intent_classifier import IntentClassifier
from ai.response_parser import ResponseParser
from ai.vision_analyzer import VisionAnalyzer
from audio.microphone import Microphone
from audio.speech_to_text import SpeechToTextService
from audio.text_to_speech import TextToSpeechService
from config.settings import Settings
from core.exceptions import AIServiceError
from core.models import ActionRequest
from orchestration.assistant import Assistant
from orchestration.command_router import CommandRouter
from utils.logging import configure_logging
from utils.audio_utils import pcm_to_audio_data
from utils.paths import ProjectPaths

configure_logging()
paths = ProjectPaths.discover()
settings = None
my_api_key = None

gemini_client = None
wakePhrase = None
general_system_prompt = None
gemini_model = None
use_gemini_tts = None
vision_system_prompt = None
wake_detector = None
CHUNK = 1024
CHANNELS = 1
RATE = 16000
SPEECH_ENERGY_THRESHOLD = 500
SILENCE_AFTER_SPEECH_SECONDS = 1.0
MAX_COMMAND_SECONDS = 5.0
microphone = None
speech_to_text_service = None
response_window = None
ui_controller = None
qt_app = None
stop_event = Event()
is_exiting = False


def build_runtime():
    global settings, my_api_key, gemini_client, wakePhrase, general_system_prompt
    global gemini_model, use_gemini_tts, vision_system_prompt, wake_detector
    global microphone, speech_to_text_service, tts_service, vision_analyzer

    settings = Settings.load(paths)
    my_api_key = settings.require_gemini_api_key()
    gemini_client = GeminiClient(api_key=my_api_key)
    print("Gemini Client connected successfully!")

    wakePhrase = settings.wake_phrase
    general_system_prompt = settings.general_system_prompt
    gemini_model = settings.gemini_model
    use_gemini_tts = settings.gemini_tts

    vision_system_prompt = """
You are the action-planning module of an AI assistant.

Analyze the screenshot and user's request.

Determine whether an internal action should be executed.

AVAILABLE ACTIONS:


add_calendar:
Add an event to the user's calendar.

Parameters:
- title: string
- date: YYYY-MM-DD
- start_time: HH:MM
- end_time: HH:MM or null
- description: string or null

describe_screen:
Describe what is visible on the user's screen when they ask what is on or in their screen.

Parameters:
- response: string

Return ONLY valid JSON:

{
    "action": "action_name",
    "data": {}
}

Rules:
- action must be one of the available actions
- data must contain the parameters for that action
- never invent missing information
- use null when information cannot be determined
- if no action is appropriate, use:
  {"action": "none", "data": {}}

STRICT OUTPUT RULES:
- Return ONLY the raw JSON object.
- DO NOT use Markdown.
- DO NOT wrap the response in ```json.
- DO NOT wrap the response in ``` or any other code fence.
- DO NOT include explanations before or after the JSON.
- DO NOT include comments inside the JSON.
- The first character of your response MUST be `{`.
- The last character of your response MUST be `}`.
- "action" must be one of the available actions.
- "data" must contain only the parameters defined for that action.
- If information cannot be determined from the screenshot, use null instead of guessing.
- If no action should be performed, return:
  {"action": "none", "data": {}}
- The response must be directly parseable using Python's json.loads().
"""

    wake_detector = WakeWordDetector(
        wake_words=[wakePhrase, "hey_jarvis"],
        vad_threshold=0.5,
    )

    microphone = Microphone(
        chunk_size=CHUNK,
        channels=CHANNELS,
        sample_rate=RATE,
    )
    speech_to_text_service = SpeechToTextService()

    def update_response_window(text):
        if ui_controller is not None:
            ui_controller.set_response(text)

    def update_scan_state(enabled):
        if ui_controller is not None:
            ui_controller.show_scan(enabled)

    tts_service = TextToSpeechService(
        use_gemini=use_gemini_tts,
        gemini_api_key=my_api_key,
        response_callback=update_response_window,
    )

    vision_analyzer = VisionAnalyzer(
        gemini_client=gemini_client,
        response_parser=ResponseParser(),
        model=gemini_model,
        system_instruction=vision_system_prompt,
        scan_callback=update_scan_state,
    )

    return {
        "settings": settings,
        "gemini_client": gemini_client,
        "wake_detector": wake_detector,
        "microphone": microphone,
        "speech_to_text_service": speech_to_text_service,
        "tts_service": tts_service,
        "vision_analyzer": vision_analyzer,
    }


def update_response_window(text):
    if ui_controller is not None:
        ui_controller.set_response(text)


def update_scan_state(enabled):
    if ui_controller is not None:
        ui_controller.show_scan(enabled)

#---------------- EXIT FUNCTION

def exits():
    global is_exiting

    if is_exiting:
        return

    is_exiting = True
    stop_event.set()
    print("Exiting...")

    if ui_controller is not None:
        ui_controller.hide()

    try:
        microphone.close()
    finally:
        tts_service.close()
        if qt_app is not None:
            qt_app.quit()


# ---------------- SPEECH TO TEXT

def speech_to_text():
    print("\nListening for your command...")

    raw_audio = microphone.record_command(
        max_seconds=MAX_COMMAND_SECONDS,
        energy_threshold=SPEECH_ENERGY_THRESHOLD,
        silence_after_seconds=SILENCE_AFTER_SPEECH_SECONDS,
    )
    audio_data = pcm_to_audio_data(raw_audio, RATE, 2)

    print("Processing transcription...")
    return speech_to_text_service.transcribe(audio_data)


# ---------------- TEXT TO SPEECH

def text_to_speech(text):
    tts_service.speak(text)


# ---------------- GENERAL ACTION FUNCTION
def general_action(parsed_data):
    response_text = parsed_data.data.get("response")
    text_to_speech(response_text)




# ---------------- MAIN LOOP

def run_assistant():
    intent_classifier = IntentClassifier(paths.intent_model_dir)
    action_registry = create_default_registry(
        computer_actions=ComputerActions(),
        calendar_actions=CalendarActions(),
        confirmation_service=ConfirmationService(text_to_speech, speech_to_text),
        speak=text_to_speech,
        on_exit=exits,
    )
    command_router = CommandRouter(
        registry=action_registry,
        intent_classifier=intent_classifier,
        gemini_client=gemini_client,
        vision_analyzer=vision_analyzer,
        model=gemini_model,
        system_instruction=general_system_prompt,
    )
    assistant = Assistant(
        wake_detector=wake_detector,
        microphone=microphone,
        speech_to_text_service=speech_to_text_service,
        router=command_router,
        tts_service=tts_service,
        ui_controller=ui_controller,
        max_command_seconds=MAX_COMMAND_SECONDS,
        speech_energy_threshold=SPEECH_ENERGY_THRESHOLD,
        silence_after_seconds=SILENCE_AFTER_SPEECH_SECONDS,
        sample_rate=RATE,
        pcm_converter=pcm_to_audio_data,
        stop_event=stop_event,
    )

    try:
        print("\nListening for wake words...\n")
        assistant.run_loop()
    except KeyboardInterrupt:
        print("\nStopping...")
        exits()


def main() -> int:
    app = QApplication(sys.argv)
    qt_app = app

    response_window = FloatingWindow()
    ui_controller = UIController(response_window)
    ui_controller.show()

    build_runtime()

    assistant_thread = Thread(target=run_assistant, daemon=True)
    assistant_thread.start()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())

