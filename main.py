import os
import win32gui
import win32con
import configparser
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
from threading import Event, Thread
from PyQt5.QtWidgets import QApplication
from openwakeword.model import Model
from myGUI import FloatingWindow
from google import genai
from dotenv import load_dotenv

load_dotenv()
my_api_key = os.getenv("GEMINI_API_KEY")

if not my_api_key:
    print("Uh oh! Python still can't find the API key.")
    exit(1)
else:
    # Pass it explicitly into the client
    client = genai.Client(api_key=my_api_key)
    print("Gemini Client connected successfully!")

# ---------------- CONFIG

config = configparser.ConfigParser()
config.read("config.ini")

wakePhrase = config["Main"]["wakephrase"]
system_prompt = config["Main"]["system_prompt"]
gemini_model = config["Main"]["gemini_model"]

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

    tts = gTTS(text=text, lang='en')
    audio_stream = io.BytesIO()

    # 3. Write the MP3 to stream
    tts.write_to_fp(audio_stream)

    # 4. Rewind the stream begin
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


# ---------------- MAIN LOOP

def run_assistant():
    with open("intentClassificationModel/models/intent_model.pkl", "rb") as f:
        intent_model = pickle.load(f)

    with open("intentClassificationModel/models/vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
    
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

                    response_window.set_visible(True)
                    text_to_speech("This is jarvis. What's up?")
                    response_window.set_visible(False)

                    command = speech_to_text()
                    
                    if command:
                        print(f"Command: {command}")
    
                        response_window.set_visible(True)
                        text_to_speech("Thinking...")

                        try:
                            interaction = client.interactions.create(
                                model="gemini-3.5-flash-lite",
                                input=command,
                                system_instruction=system_prompt
                            )
                            response_text = interaction.output_text

                            if not response_text:
                                raise RuntimeError("Gemini returned an empty response")

                            print("[LOG] Gemini Response:", response_text)
                            text_to_speech(response_text)
                        except Exception as error:
                            print(f"[ERROR] Gemini request failed: {error}")
                            text_to_speech("I could not get a response from Gemini.")

                    # Hide UI after processing the command
                    response_window.set_visible(False)

                    print("\nListening for wake words...\n")

                    wake_model.reset()

                    break


                elif mdl == wakePhrase and score > 0.5:
                    print(f"\nWakeword detected! Score: {score:.3f}")

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

