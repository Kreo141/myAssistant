"""Gemini API boundary."""

from __future__ import annotations

from typing import Any

from google import genai
from google.genai import types

from core.exceptions import AIServiceError


class GeminiClient:
    def __init__(self, api_key: str, client: Any | None = None) -> None:
        self._client = client or genai.Client(api_key=api_key)

    def generate_chat(
        self,
        model: str,
        prompt: str,
        system_instruction: str,
    ) -> str:
        try:
            interaction = self._client.interactions.create(
                model=model,
                input=prompt,
                system_instruction=system_instruction,
            )
        except Exception as error:
            raise AIServiceError("Gemini chat request failed") from error

        response_text = getattr(interaction, "output_text", None)
        if not response_text:
            raise AIServiceError("Gemini returned an empty chat response")
        return response_text

    def generate_vision(
        self,
        model: str,
        image_bytes: bytes,
        image_mime_type: str,
        prompt: str,
        system_instruction: str,
    ) -> str:
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(
                        mime_type=image_mime_type,
                        data=image_bytes,
                    ),
                    types.Part.from_text(
                        text=f"SYSTEM INSTRUCTION: {system_instruction}\n USER PROMPT: {prompt}"
                    ),
                ],
            )
        ]

        try:
            interaction = self._client.models.generate_content(
                model=model,
                contents=contents,
            )
        except Exception as error:
            raise AIServiceError("Gemini vision request failed") from error

        response_text = getattr(interaction, "text", None)
        if not response_text:
            raise AIServiceError("Gemini returned an empty vision response")
        return response_text

    def generate_tts(
        self,
        text: str,
        model: str,
        voice_name: str,
    ) -> tuple[bytes, str]:
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=text)],
            ),
        ]
        config = types.GenerateContentConfig(
            temperature=1,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name,
                    )
                )
            ),
        )

        audio_data = bytearray()
        mime_type = ""
        try:
            response = self._client.models.generate_content_stream(
                model=model,
                contents=contents,
                config=config,
            )
            for chunk in response:
                if not chunk.parts:
                    continue
                inline_data = chunk.parts[0].inline_data
                if inline_data and inline_data.data:
                    audio_data.extend(inline_data.data)
                    mime_type = inline_data.mime_type or mime_type
        except Exception as error:
            raise AIServiceError("Gemini TTS request failed") from error

        if not audio_data:
            raise AIServiceError("Gemini TTS returned no audio data")
        return bytes(audio_data), mime_type