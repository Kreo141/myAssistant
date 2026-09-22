"""Application-specific exception types."""


class AssistantError(Exception):
    """Base exception for expected assistant failures."""


class ConfigurationError(AssistantError):
    """Raised when application configuration is missing or invalid."""


class AudioError(AssistantError):
    """Raised when audio input or output cannot be used."""


class AIServiceError(AssistantError):
    """Raised when an external or local AI service fails."""


class StorageError(AssistantError):
    """Raised when persistent data cannot be read or written."""


class ActionError(AssistantError):
    """Raised when an assistant action cannot be completed."""