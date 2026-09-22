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
from audio.wake_word import WakeWordDetector
from config.settings import Settings
from core.exceptions import AIServiceError
from core.models import ActionRequest
from utils.logging import configure_logging
from utils.audio_utils import pcm_to_audio_data
from utils.paths import ProjectPaths

configure_logging()
paths = ProjectPaths.discover()
settings = Settings.load(paths)
my_api_key = settings.require_gemini_api_key()

gemini_client = GeminiClient(api_key=my_api_key)
print("Gemini Client connected successfully!")

# ---------------- CONFIG

wakePhrase = settings.wake_phrase
general_system_prompt = settings.general_system_prompt
gemini_model = settings.gemini_model
# vision_system_prompt = config["Main"]["vision_system_prompt"]
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

# ---------------- WAKE WORD

wake_detector = WakeWordDetector(
    wake_words=[wakePhrase, "hey_jarvis"],
    vad_threshold=0.5,
)

# ---------------- AUDIO

CHUNK = 1024
CHANNELS = 1
RATE = 16000
SPEECH_ENERGY_THRESHOLD = 500
SILENCE_AFTER_SPEECH_SECONDS = 1.0
MAX_COMMAND_SECONDS = 5.0

microphone = Microphone(
    chunk_size=CHUNK,
    channels=CHANNELS,
    sample_rate=RATE,
)

speech_to_text_service = SpeechToTextService()
response_window = None
ui_controller = None
qt_app = None
stop_event = Event()
is_exiting = False


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
    
    try:
        print("\nListening for wake words...\n")

        while not stop_event.is_set():
            # Read microphone
            data = microphone.read_chunk()

            audio_data = np.frombuffer(
                data,
                dtype=np.int16
            )

            # Run wake-word detection
            wake_scores = wake_detector.predict(audio_data)

            # Check wake word
            for mdl, score in wake_scores.items():

                if mdl == "hey_jarvis" and score > 0.5:
                    print(f"\n(Jarvis) Wakeword detected! Score: {score:.3f}")

                    if ui_controller is not None:
                        ui_controller.show_wake_indicator()
                    text_to_speech("Hey!")
                    if ui_controller is not None:
                        ui_controller.hide()

                    command = speech_to_text()
                    
                    if command:
                        genai_intent = intent_classifier.classify_gemini_task(command)

                        print(f"[{genai_intent}] Command: {command}")

                        
                        if genai_intent == "general_chat": 
                            try:
                                if ui_controller is not None:
                                    ui_controller.show()
                                text_to_speech("Thinking...")
                                response_text = gemini_client.generate_chat(
                                    model=gemini_model,
                                    prompt=command,
                                    system_instruction=general_system_prompt,
                                )

                                print("[LOG] Gemini Response:", response_text)
                                text_to_speech(response_text)
                            except Exception as error:
                                print(f"[ERROR] Gemini request failed: {error}")
                                text_to_speech("I could not get a response from Gemini.")
                                
                        elif genai_intent == "analyze_screen":
                            try:
                                action_request = vision_analyzer.analyze(command)
                                print("[LOG] Gemini action:", action_request)

                                if action_request.name == "describe_screen":
                                    general_action(action_request)

                                if action_request.name == "add_calendar":
                                    result = action_registry.dispatch(action_request)
                                    if result.message:
                                        text_to_speech(result.message)
                            except AIServiceError as error:
                                print(f"[ERROR] Vision request failed: {error}")
                                text_to_speech("I could not analyze the screen.")
                        

                    # Hide UI after processing the command
                    if ui_controller is not None:
                        ui_controller.hide()

                    print("\nListening for wake words...\n")

                    wake_detector.reset()

                    break


                elif mdl == wakePhrase and score > 0.5:
                    print(f"\nWakeword detected! Score: {score:.3f}")

                    if ui_controller is not None:
                        ui_controller.show_wake_indicator()
                    text_to_speech("What's up?")
                    if ui_controller is not None:
                        ui_controller.hide()

                    text = speech_to_text()

                    if text:
                        print(f"Command: {text}")

                        intent = intent_classifier.classify_local(text)

                        result = action_registry.dispatch(ActionRequest(name=intent))
                        if result.data.get("exit"):
                            return

                    # Hide UI after processing the command
                    if ui_controller is not None:
                        ui_controller.hide()

                    print("\nListening for wake words...\n")

                    wake_detector.reset()

                    break

    except KeyboardInterrupt:
        print("\nStopping...")
        exits()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qt_app = app
    response_window = FloatingWindow()
    ui_controller = UIController(response_window)
    ui_controller.show()

    assistant_thread = Thread(target=run_assistant, daemon=True)
    assistant_thread.start()

    sys.exit(app.exec_())

