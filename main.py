import os
import configparser
import pyaudio
import numpy as np
import openwakeword
import speech_recognition as sr
from gtts import gTTS
import pygame
import io
import pickle
from openwakeword.model import Model

# ---------------- CONFIG

config = configparser.ConfigParser()
config.read("config.ini")

wakePhrase = config["Main"]["wakephrase"]

# ---------------- WAKE WORD

openwakeword.utils.download_models()

wake_model = Model(
    wakeword_models=[wakePhrase],
    vad_threshold=0.5
)

# ---------------- AUDIO

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

audio = pyaudio.PyAudio()

mic_stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK
)

recognizer = sr.Recognizer()

def exits():
    print("Exiting...")
    mic_stream.stop_stream()
    mic_stream.close()
    audio.terminate()
    exit(0)


# ---------------- SPEECH TO TEXT

def speech_to_text():
    print("\nListening for your command...")

    frames = []

    for _ in range(int(RATE / CHUNK * 5)):
        data = mic_stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

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


# ---------------- MAIN LOOP

if __name__ == "__main__":
    with open("intentClassificationModel/models/intent_model.pkl", "rb") as f:
        intent_model = pickle.load(f)

    with open("intentClassificationModel/models/vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
    
    try:
        print("\nListening for wake words...\n")

        while True:
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

                if score > 0.5:
                    print(f"\nWakeword detected! Score: {score:.3f}")

                    text_to_speech("Yes?")

                    # Capture speech
                    text = speech_to_text()

                    if text:
                        print(f"Command: {text}")

                        X = vectorizer.transform([text])
                        intent = intent_model.predict(X)[0]

                        if intent == "greetings":
                            text_to_speech("Hello! How can I assist you?")

                        if intent == "lock_computer":
                            text_to_speech("Locking the computer...")

                        if intent == "shutdown_computer":
                            text_to_speech("Shutting down the computer...")

                        if intent == "close_all_windows":
                            text_to_speech("Closing all windows...")

                        if intent == "exit": 
                            text_to_speech("Are you sure you want to exit?")
                            response = speech_to_text()

                            if response and "yes" in response.lower():
                                text_to_speech("Exiting...")
                                exits()

                            text_to_speech("Okay!")

                    print("\nListening for wake words...\n")

                    wake_model.prediction_buffer.clear()

                    break

    except KeyboardInterrupt:
        print("\nStopping...")
        exits()

