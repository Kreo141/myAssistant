import configparser
import pyaudio
import openwakeword
from openwakeword.model import Model

config = configparser.ConfigParser()
config.read("config.ini")

# --------------/ Config Variables
wakePhrase = config["Main"]["wakephrase"]
# ---/

openwakeword.utils.download_models()

model = Model(
    wakeword_models=[wakePhrase],
    vad_threshold=0.5
)

frame = mm