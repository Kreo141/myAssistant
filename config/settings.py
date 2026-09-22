"""Typed application settings loaded from config.ini and the environment."""

from __future__ import annotations

import configparser
import os
from dataclasses import dataclass

from dotenv import load_dotenv

from core.exceptions import ConfigurationError
from utils.paths import ProjectPaths


@dataclass(frozen=True)
class Settings:
    wake_phrase: str
    sensitivity: float
    general_system_prompt: str
    vision_system_prompt: str
    gemini_model: str
    gemini_tts: bool
    gemini_api_key: str | None

    @classmethod
    def load(cls, paths: ProjectPaths) -> "Settings":
        load_dotenv(dotenv_path=paths.env_file)

        parser = configparser.ConfigParser()
        if not parser.read(paths.config_file):
            raise ConfigurationError(
                f"Configuration file was not found: {paths.config_file}"
            )

        if "Main" not in parser:
            raise ConfigurationError("The configuration file is missing the [Main] section")

        section = parser["Main"]
        try:
            return cls(
                wake_phrase=section["wakephrase"],
                sensitivity=section.getfloat("sensitivity", fallback=0.5),
                general_system_prompt=section["general_system_prompt"],
                vision_system_prompt=section.get("vision_system_prompt", fallback=""),
                gemini_model=section["gemini_model"],
                gemini_tts=section.getboolean("gemini_tts", fallback=False),
                gemini_api_key=os.getenv("GEMINI_API_KEY"),
            )
        except (KeyError, ValueError) as error:
            raise ConfigurationError(
                f"Invalid setting in configuration file: {error}"
            ) from error

    def require_gemini_api_key(self) -> str:
        if not self.gemini_api_key:
            raise ConfigurationError("GEMINI_API_KEY was not found in the environment")
        return self.gemini_api_key