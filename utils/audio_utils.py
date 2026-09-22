"""Pure audio data helpers."""

from __future__ import annotations

import re
import struct

import numpy as np
import speech_recognition as sr


def calculate_rms_energy(audio_data: bytes, sample_width: int = 2) -> float:
    samples = np.frombuffer(audio_data, dtype=np.int16 if sample_width == 2 else np.int8)
    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))


def pcm_to_audio_data(
    audio_data: bytes,
    sample_rate: int,
    sample_width: int,
) -> sr.AudioData:
    return sr.AudioData(audio_data, sample_rate, sample_width)


def parse_audio_mime_type(mime_type: str) -> dict[str, int]:
    bits_per_sample = 16
    sample_rate = 24000

    for parameter in mime_type.split(";"):
        parameter = parameter.strip()
        rate_match = re.fullmatch(r"rate\s*=\s*(\d+)", parameter, re.IGNORECASE)
        format_match = re.fullmatch(r"audio/l(\d+)", parameter, re.IGNORECASE)

        if rate_match:
            sample_rate = int(rate_match.group(1))
        elif format_match:
            bits_per_sample = int(format_match.group(1))

    if bits_per_sample <= 0 or bits_per_sample % 8 != 0:
        raise ValueError("Audio MIME type contains an invalid bit depth")
    if sample_rate <= 0:
        raise ValueError("Audio MIME type contains an invalid sample rate")

    return {
        "bits_per_sample": bits_per_sample,
        "rate": sample_rate,
    }


def pcm_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    block_align = num_channels * (bits_per_sample // 8)
    byte_rate = sample_rate * block_align

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )
    return header + audio_data