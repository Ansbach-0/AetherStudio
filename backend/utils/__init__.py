"""
Módulo de utilitários.

Contém funções auxiliares, logging e tratamento de exceções.
"""

from backend.utils.logger import get_logger, setup_logging
from backend.utils.exceptions import (
    VoiceCloneException,
    AudioValidationError,
    InsufficientCreditsError,
    UserNotFoundError,
    VoiceProfileNotFoundError,
)
from backend.utils.validators import (
    validate_email,
    validate_language,
    validate_audio_format,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "VoiceCloneException",
    "AudioValidationError",
    "InsufficientCreditsError",
    "UserNotFoundError",
    "VoiceProfileNotFoundError",
    "validate_email",
    "validate_language",
    "validate_audio_format",
]
