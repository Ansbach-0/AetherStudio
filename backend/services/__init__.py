"""
Módulo de serviços de negócio.

Contém a lógica de negócio para processamento de áudio,
clonagem de voz e gerenciamento de créditos.
"""

from backend.services.audio_processor import AudioProcessor
from backend.services.credits_service import CreditsService
from backend.services.tts_service import TTSService
from backend.services.rvc_service import RVCService
from backend.services.language_detector import LanguageDetector, get_language_detector
from backend.services.voice_pipeline import VoicePipeline, get_voice_pipeline, initialize_pipeline
from backend.services.payment_service import PaymentService, get_payment_service
from backend.services.cache_service import AudioCacheService, MemoryCache, get_cache_service
from backend.services.background_tasks import BackgroundTaskManager, TaskStatus, get_task_manager
from backend.services.training_service import TrainingService, TrainingStatus, get_training_service
from backend.services.webhook_service import WebhookService, WebhookEvent, get_webhook_service

__all__ = [
    "AudioProcessor",
    "CreditsService",
    "TTSService",
    "RVCService",
    "LanguageDetector",
    "get_language_detector",
    "VoicePipeline",
    "get_voice_pipeline",
    "initialize_pipeline",
    "PaymentService",
    "get_payment_service",
    "AudioCacheService",
    "MemoryCache",
    "get_cache_service",
    "BackgroundTaskManager",
    "TaskStatus",
    "get_task_manager",
    "TrainingService",
    "TrainingStatus",
    "get_training_service",
    "WebhookService",
    "WebhookEvent",
    "get_webhook_service",
]
