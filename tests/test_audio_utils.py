import struct
import unittest

from utils.audio_utils import calculate_rms_energy, pcm_to_audio_data


class AudioUtilsTests(unittest.TestCase):
    def test_calculate_rms_energy_for_empty_audio(self):
        self.assertEqual(calculate_rms_energy(b""), 0.0)

    def test_calculate_rms_energy_for_pcm_samples(self):
        audio_data = struct.pack("<hhhh", 100, -100, 100, -100)

        self.assertEqual(calculate_rms_energy(audio_data), 100.0)

    def test_pcm_to_audio_data_preserves_format(self):
        audio_data = pcm_to_audio_data(b"pcm", 16000, 2)

        self.assertEqual(audio_data.sample_rate, 16000)
        self.assertEqual(audio_data.sample_width, 2)
        self.assertEqual(audio_data.frame_data, b"pcm")


if __name__ == "__main__":
    unittest.main()