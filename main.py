import win32gui
import win32con
import json
import pyaudio
import numpy as np
import openwakeword
import speech_recognition as sr
from gtts import gTTS
import pygame
import io
import pickle
import ctypes
import sys
import pyautogui
from threading import Event, Thread
from PyQt5.QtWidgets import QApplication
from openwakeword.model import Model
from myGUI import FloatingWindow
from google import genai
from google.genai import types
from text_to_speech import TextToSpeechGenerator
from config.settings import Settings
from utils.logging import configure_logging
from utils.paths import ProjectPaths

configure_logging()
paths = ProjectPaths.discover()
settings = Settings.load(paths)
my_api_key = settings.require_gemini_api_key()

client = genai.Client(api_key=my_api_key)
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

openwakeword.utils.download_models()

wake_model = Model(
    wakeword_models=[wakePhrase, "hey_jarvis"],
    vad_threshold=0.5
)

# ---------------- AUDIO

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
SPEECH_ENERGY_THRESHOLD = 500
SILENCE_AFTER_SPEECH_SECONDS = 1.0
MAX_COMMAND_SECONDS = 5.0

audio = pyaudio.PyAudio()

mic_stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK
)

recognizer = sr.Recognizer()
response_window = None
qt_app = None
stop_event = Event()
is_exiting = False

#---------------- EXIT FUNCTION

def exits():
    global is_exiting

    if is_exiting:
        return

    is_exiting = True
    stop_event.set()
    print("Exiting...")

    if response_window is not None:
        response_window.set_visible(False)

    try:
        if mic_stream.is_active():
            mic_stream.stop_stream()
        mic_stream.close()
    finally:
        audio.terminate()
        pygame.mixer.quit()
        if qt_app is not None:
            qt_app.quit()


# ---------------- SPEECH TO TEXT

def speech_to_text():
    print("\nListening for your command...")

    frames = []
    speech_started = False
    silence_duration = 0.0
    chunk_duration = CHUNK / RATE

    for _ in range(int(MAX_COMMAND_SECONDS / chunk_duration)):
        data = mic_stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

        samples = np.frombuffer(data, dtype=np.int16)
        energy = np.sqrt(np.mean(samples.astype(np.float32) ** 2))

        if energy >= SPEECH_ENERGY_THRESHOLD:
            speech_started = True
            silence_duration = 0.0
        elif speech_started:
            silence_duration += chunk_duration
            if silence_duration >= SILENCE_AFTER_SPEECH_SECONDS:
                break

    # Convert recorded data into SpeechRecognition AudioData
    raw_audio = b"".join(frames)

    audio_data = sr.AudioData(
        raw_audio,
        RATE,
        2
    )

    print("Processing transcription...")

    try:
        text = recognizer.recognize_google(audio_data)
        print(f"You said: {text}")
        return text

    except sr.UnknownValueError:
        print("Could not understand the audio.")

    except sr.RequestError as e:
        print(f"Google Speech Recognition error: {e}")

    return None


# ---------------- TEXT TO SPEECH

def text_to_speech(text):
    if response_window is not None:
        response_window.set_response(text)

    if use_gemini_tts:
        try:
            audio_data = TextToSpeechGenerator.generate(text)
            audio_stream = io.BytesIO(audio_data)
        except Exception as error:
            print(f"[ERROR] Gemini TTS failed, using Google TTS: {error}")
            audio_stream = io.BytesIO()
            gTTS(text=text, lang="en").write_to_fp(audio_stream)
            audio_stream.seek(0)
    else:
        tts = gTTS(text=text, lang="en")
        audio_stream = io.BytesIO()
        tts.write_to_fp(audio_stream)
        audio_stream.seek(0)

    # 5. Init mixer
    pygame.mixer.init()

    # 6. Load audio and play
    pygame.mixer.music.load(audio_stream)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.wait(100)


# ---------------- CONFIRM ACTION
def confirm_action(prompt="Are you sure you want to do this?"):
    text_to_speech(prompt)
    response = speech_to_text()

    if response and "yes" in response.lower():
        return True

    return False


# ---------------- CLOSE WINDOW
def close_window(hwnd, extra):
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if title and title not in ["Program Manager", "Settings"]:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)


# ---------------- GENERAL ACTION FUNCTION
def general_action(parsed_data):
    response_text = parsed_data["data"].get("response")
    text_to_speech(response_text)




# ---------------- GENERAL ASSISTANT FUNCTION



# ---------------- VISION ASSISSTANT FUNCTION
def analyze_screen_with_gemini(prompt):
    screenshot = pyautogui.screenshot()

    image_buffer = io.BytesIO()

    screenshot.save(image_buffer, format="JPEG")

    image_bytes = image_buffer.getvalue()

    model = gemini_model
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    mime_type="image/png",
                    data=image_bytes,
                ),
                types.Part.from_text(
                    text=
                    f"SYSTEM INSTRUCTION: {vision_system_prompt}\n USER PROMPT: {prompt}"),
            ],
        ),
    ]

    response_window.trigger_scan(True)

    interaction = client.models.generate_content(
        model=model,
        contents=contents
    )

    print("[LOG]: " + str(interaction))
    response_text = interaction.text if interaction.text else "No response from Gemini."

    response_window.trigger_scan(False)
    return response_text



# ---------------- MAIN LOOP

def run_assistant():
    with open(paths.intent_model_dir / "intent_model_intent.pkl", "rb") as f:
        intent_model = pickle.load(f)

    with open(paths.intent_model_dir / "vectorizer_intent.pkl", "rb") as f:
        vectorizer = pickle.load(f)

    with open(paths.intent_model_dir / "intent_model_genai_task_intent.pkl", "rb") as f:
        genai_task_intent_model = pickle.load(f)

    with open(paths.intent_model_dir / "vectorizer_genai_task_intent.pkl", "rb") as f:
        genai_task_vectorizer = pickle.load(f)
    
    try:
        print("\nListening for wake words...\n")

        while not stop_event.is_set():
            # Read microphone
            data = mic_stream.read(
                CHUNK,
                exception_on_overflow=False
            )

            audio_data = np.frombuffer(
                data,
                dtype=np.int16
            )

            # Run wake-word detection
            wake_model.predict(audio_data)

            # Check wake word
            for mdl in wake_model.prediction_buffer.keys():
                scores = list(wake_model.prediction_buffer[mdl])
                score = scores[-1]

                if mdl == "hey_jarvis" and score > 0.5:
                    print(f"\n(Jarvis) Wakeword detected! Score: {score:.3f}")

                    response_window.trigger_wave()
                    response_window.set_visible(True)
                    text_to_speech("Hey!")
                    response_window.set_visible(False)

                    command = speech_to_text()
                    
                    if command:
                        X = genai_task_vectorizer.transform([command])
                        genai_intent = genai_task_intent_model.predict(X)[0]

                        print(f"[{genai_intent}] Command: {command}")

                        
                        if genai_intent == "general_chat": 
                            try:
                                response_window.set_visible(True)
                                text_to_speech("Thinking...")
                                interaction = client.interactions.create(
                                    model=gemini_model,
                                    input=command,
                                    system_instruction=general_system_prompt
                                )
                                response_text = interaction.output_text
    
                                if not response_text:
                                    raise RuntimeError("Gemini returned an empty response")
    
                                print("[LOG] Gemini Response:", response_text)
                                text_to_speech(response_text)
                            except Exception as error:
                                print(f"[ERROR] Gemini request failed: {error}")
                                text_to_speech("I could not get a response from Gemini.")
                                
                        elif genai_intent == "analyze_screen":
                            # Implement: Analyze the screen content and provide insights
                            response = analyze_screen_with_gemini(command)

                            print("[LOG] Gemini Response:", response)

                            parsed_data = json.loads(response)

                            if parsed_data.get("action") == "describe_screen":
                                general_action(parsed_data)

                            if parsed_data.get("action") == "add_calendar":
                                # Implement: Add event to calendar
                                print()
                        

                    # Hide UI after processing the command
                    response_window.set_visible(False)

                    print("\nListening for wake words...\n")

                    wake_model.reset()

                    break


                elif mdl == wakePhrase and score > 0.5:
                    print(f"\nWakeword detected! Score: {score:.3f}")

                    response_window.trigger_wave()
                    response_window.set_visible(True)
                    text_to_speech("What's up?")
                    response_window.set_visible(False)

                    text = speech_to_text()

                    if text:
                        print(f"Command: {text}")

                        X = vectorizer.transform([text])
                        intent = intent_model.predict(X)[0]

                        if intent == "greetings":
                            text_to_speech("Hello! How can I assist you?")
                            response_window.set_visible(True)

                        if intent == "lock_computer":
                            text_to_speech("Locking the computer...")
                            ctypes.windll.user32.LockWorkStation()

                        if intent == "shutdown_computer":
                            if confirm_action("Are you sure you want to do this?"):
                                text_to_speech("Shutting down...")
                                # os.system("shutdown /s /t 1")

                        if intent == "close_all_windows":
                            # Iterate through all top-level windows
                            win32gui.EnumWindows(close_window, None)

                        if intent == "exit": 
                            if confirm_action("Are you sure you want to exit?"):
                                text_to_speech("Exiting...")
                                exits()
                                return

                            text_to_speech("Okay!")

                    # Hide UI after processing the command
                    response_window.set_visible(False)

                    print("\nListening for wake words...\n")

                    wake_model.reset()

                    break

    except KeyboardInterrupt:
        print("\nStopping...")
        exits()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qt_app = app
    response_window = FloatingWindow()
    response_window.show()

    assistant_thread = Thread(target=run_assistant, daemon=True)
    assistant_thread.start()

    sys.exit(app.exec_())

