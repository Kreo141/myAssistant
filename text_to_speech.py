# To run this code you need to install the following dependencies:
# pip install google-genai

import os
import struct
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class TextToSpeechGenerator:
    @staticmethod
    def generate(text):
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
        )

        model = "gemini-3.1-flash-tts-preview"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=text),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            response_modalities=[
                "audio",
            ],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Iapetus"
                    )
                )
            ),
        )

        audio_data = bytearray()
        mime_type = ""
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.parts is None
            ):
                continue
            if chunk.parts[0].inline_data and chunk.parts[0].inline_data.data:
                inline_data = chunk.parts[0].inline_data
                audio_data.extend(inline_data.data)
                mime_type = inline_data.mime_type
            else:
                if text := chunk.text:
                    print(text)
        if not audio_data:
            raise RuntimeError("Gemini TTS returned no audio data")

        return TextToSpeechGenerator.convert_to_wav(bytes(audio_data), mime_type)

    @staticmethod
    def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
        """Generates a WAV file header for the given audio data and parameters.

        Args:
            audio_data: The raw audio data as a bytes object.
            mime_type: Mime type of the audio data.

        Returns:
            A bytes object representing the WAV file header.
        """
        parameters = TextToSpeechGenerator.parse_audio_mime_type(mime_type)
        bits_per_sample = parameters["bits_per_sample"]
        sample_rate = parameters["rate"]
        num_channels = 1
        data_size = len(audio_data)
        bytes_per_sample = bits_per_sample // 8
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

        # http://soundfile.sapp.org/doc/WaveFormat/

        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",          # ChunkID
            chunk_size,       # ChunkSize (total file size - 8 bytes)
            b"WAVE",          # Format
            b"fmt ",          # Subchunk1ID
            16,               # Subchunk1Size (16 for PCM)
            1,                # AudioFormat (1 for PCM)
            num_channels,     # NumChannels
            sample_rate,      # SampleRate
            byte_rate,        # ByteRate
            block_align,      # BlockAlign
            bits_per_sample,  # BitsPerSample
            b"data",          # Subchunk2ID
            data_size         # Subchunk2Size (size of audio data)
        )
        return header + audio_data

    @staticmethod
    def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
        """Parses bits per sample and rate from an audio MIME type string.

        Assumes bits per sample is encoded like "L16" and rate as "rate=xxxxx".

        Args:
            mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000").

        Returns:
            A dictionary with "bits_per_sample" and "rate" keys. Values will be
            integers if found, otherwise None.
        """
        bits_per_sample = 16
        rate = 24000

        # Extract rate from parameters
        parts = mime_type.split(";")
        for param in parts: # Skip the main type part
            param = param.strip()
            if param.lower().startswith("rate="):
                try:
                    rate_str = param.split("=", 1)[1]
                    rate = int(rate_str)
                except (ValueError, IndexError):
                    # Handle cases like "rate=" with no value or non-integer value
                    pass # Keep rate as default
            elif param.startswith("audio/L"):
                try:
                    bits_per_sample = int(param.split("L", 1)[1])
                except (ValueError, IndexError):
                    pass # Keep bits_per_sample as default if conversion fails

        return {"bits_per_sample": bits_per_sample, "rate": rate}


