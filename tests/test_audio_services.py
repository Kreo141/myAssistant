import unittest

from audio.microphone import Microphone
from audio.speech_to_text import SpeechToTextService
from audio.wake_word import WakeWordDetector
from utils.audio_utils import pcm_to_audio_data


class FakeStream:
    def __init__(self, chunks):
        self.chunks = iter(chunks)
        self.closed = False

    def read(self, chunk_size, exception_on_overflow=False):
        return next(self.chunks)

    def is_active(self):
        return not self.closed

    def stop_stream(self):
        pass

    def close(self):
        self.closed = True


class FakeAudio:
    def __init__(self, stream):
        self.stream = stream
        self.terminated = False

    def open(self, **kwargs):
        return self.stream

    def terminate(self):
        self.terminated = True


class FakeWakeWordModel:
    def __init__(self):
        self.prediction_buffer = {"alexa": [0.2], "hey_jarvis": [0.8]}
        self.reset_called = False

    def predict(self, audio_data):
        pass

    def reset(self):
        self.reset_called = True


class FakeRecognizer:
    def recognize_google(self, audio_data):
        return "test command"


class AudioServiceTests(unittest.TestCase):
    def test_microphone_records_until_silence_and_closes_stream(self):
        loud_chunk = b"\xff\x7f" * 1024
        silent_chunk = b"\x00\x00" * 1024
        stream = FakeStream([loud_chunk, silent_chunk])
        microphone = Microphone(audio=FakeAudio(stream))

        recorded = microphone.record_command(
            max_seconds=1.0,
            energy_threshold=500,
            silence_after_seconds=0.06,
        )
        microphone.close()

        self.assertEqual(recorded, loud_chunk + silent_chunk)
        self.assertTrue(stream.closed)

    def test_wake_word_detector_returns_latest_scores(self):
        model = FakeWakeWordModel()
        detector = WakeWordDetector(["alexa", "hey_jarvis"], model=model)

        scores = detector.predict(b"audio")
        detector.reset()

        self.assertEqual(scores, {"alexa": 0.2, "hey_jarvis": 0.8})
        self.assertTrue(model.reset_called)

    def test_speech_to_text_delegates_to_recognizer(self):
        service = SpeechToTextService(FakeRecognizer())

        text = service.transcribe(pcm_to_audio_data(b"audio", 16000, 2))

        self.assertEqual(text, "test command")


if __name__ == "__main__":
    unittest.main()