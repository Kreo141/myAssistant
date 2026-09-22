import unittest

from audio.text_to_speech import TextToSpeechService
from utils.audio_utils import parse_audio_mime_type, pcm_to_wav


class FakeMusic:
    def __init__(self):
        self.loaded_audio = None
        self.play_count = 0

    def load(self, audio_stream):
        self.loaded_audio = audio_stream.read()

    def play(self):
        self.play_count += 1

    def get_busy(self):
        return False


class FakeMixer:
    def __init__(self):
        self.music = FakeMusic()
        self.init_count = 0
        self.quit_count = 0

    def init(self):
        self.init_count += 1

    def quit(self):
        self.quit_count += 1


class FakeProvider:
    def __init__(self, audio_data=b"audio"):
        self.audio_data = audio_data
        self.calls = 0

    def generate(self, text):
        self.calls += 1
        return self.audio_data


class FailingProvider:
    def generate(self, text):
        raise RuntimeError("provider unavailable")


class TextToSpeechTests(unittest.TestCase):
    def test_parse_audio_mime_type_is_case_insensitive(self):
        self.assertEqual(
            parse_audio_mime_type("audio/L24;rate=48000"),
            {"bits_per_sample": 24, "rate": 48000},
        )

    def test_pcm_to_wav_contains_pcm_header_and_data(self):
        wav_data = pcm_to_wav(b"pcm", "audio/L16;rate=16000")

        self.assertEqual(wav_data[:4], b"RIFF")
        self.assertEqual(wav_data[8:12], b"WAVE")
        self.assertTrue(wav_data.endswith(b"pcm"))

    def test_google_provider_is_played_when_gemini_is_disabled(self):
        google_provider = FakeProvider(b"google")
        mixer = FakeMixer()
        service = TextToSpeechService(
            use_gemini=False,
            google_provider=google_provider,
            mixer=mixer,
        )

        service.speak("hello")

        self.assertEqual(google_provider.calls, 1)
        self.assertEqual(mixer.music.loaded_audio, b"google")
        self.assertEqual(mixer.music.play_count, 1)
        self.assertEqual(mixer.quit_count, 1)

    def test_google_provider_is_used_when_gemini_fails(self):
        google_provider = FakeProvider(b"fallback")
        mixer = FakeMixer()
        service = TextToSpeechService(
            use_gemini=True,
            gemini_provider=FailingProvider(),
            google_provider=google_provider,
            mixer=mixer,
        )

        service.speak("hello")

        self.assertEqual(google_provider.calls, 1)
        self.assertEqual(mixer.music.loaded_audio, b"fallback")


if __name__ == "__main__":
    unittest.main()