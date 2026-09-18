import configparser
import pyaudio
import numpy as np
import openwakeword
from openwakeword.model import Model

config = configparser.ConfigParser()
config.read("config.ini")

# --------------/ Config Variables
wakePhrase = config["Main"]["wakephrase"]
# ---/

openwakeword.utils.download_models()

model = Model(
    wakeword_models=["hey_jarvis"],
    vad_threshold=0.5
)

n_models = len(model.models.keys())

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

audio = pyaudio.PyAudio()
mic_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)


try:
    print("\n\n")
    print("Listening for wake words")
    while True:
        audio = np.frombuffer(mic_stream.read(CHUNK), dtype=np.int16)

        prediction = model.predict(audio)

                # Column titles
        n_spaces = 16
        output_string_header = """
            Model Name         | Score | Wakeword Status
            --------------------------------------
            """

        for mdl in model.prediction_buffer.keys():
            # Add scores in formatted table
            scores = list(model.prediction_buffer[mdl])
            curr_score = format(scores[-1], '.20f').replace("-", "")

            output_string_header += f"""{mdl}{" "*(n_spaces - len(mdl))}   | {curr_score[0:5]} | {"--"+" "*20 if scores[-1] <= 0.5 else "Wakeword Detected!"}
            """

        # Print results table
        print("\033[F"*(4*n_models+1))
        print(output_string_header, "                             ", end='\r')

except KeyboardInterrupt:
    print()