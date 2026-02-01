"""
Serviço de transcrição de áudio usando Whisper.

Fornece transcrição automática para áudios de referência,
essencial para o correto funcionamento do F5-TTS.
"""

import asyncio
from functools import lru_cache
from pathlib import Path
from typing import Optional

from backend.utils.logger import get_logger
from backend.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

# Tentar importar Whisper
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None


class TranscriptionService:
    """
    Serviço de transcrição de áudio usando OpenAI Whisper.
    
    Usado para transcrever automaticamente áudios de referência
    quando o usuário não fornece a transcrição manualmente.
    
    F5-TTS REQUER que o ref_text corresponda exatamente ao
    conteúdo falado no áudio de referência para gerar áudio
    de qualidade.
    """
    
    # Modelo Whisper a usar (base é um bom balanço velocidade/qualidade)
    # Opções: tiny, base, small, medium, large
    MODEL_NAME = "base"
    
    def __init__(self):
        """Inicializa o serviço de transcrição."""
        self.model = None
        self.is_loaded = False
        self._loading = False
        
        if not WHISPER_AVAILABLE:
            logger.warning("OpenAI Whisper não está instalado. Transcrição automática desabilitada.")
    
    async def load_model(self) -> bool:
        """
        Carrega o modelo Whisper.
        
        Returns:
            bool: True se carregado com sucesso
        """
        if self.is_loaded:
            return True
        
        if self._loading:
            # Aguardar carregamento em andamento
            while self._loading:
                await asyncio.sleep(0.1)
            return self.is_loaded
        
        if not WHISPER_AVAILABLE:
            logger.error("Whisper não disponível para carregar")
            return False
        
        try:
            self._loading = True
            logger.info(f"Carregando modelo Whisper '{self.MODEL_NAME}'...")
            
            # Carregar em thread separada (operação bloqueante)
            self.model = await asyncio.to_thread(
                whisper.load_model,
                self.MODEL_NAME,
                device="cpu"  # CPU para compatibilidade
            )
            
            self.is_loaded = True
            logger.info(f"Modelo Whisper '{self.MODEL_NAME}' carregado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar Whisper: {e}")
            return False
        finally:
            self._loading = False
    
    async def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> Optional[str]:
        """
        Transcreve um arquivo de áudio.
        
        Args:
            audio_path: Caminho para o arquivo de áudio
            language: Código do idioma (opcional, auto-detecta se None)
                     Use códigos ISO 639-1: 'pt', 'en', 'es', etc.
        
        Returns:
            str: Texto transcrito ou None se falhar
        """
        if not WHISPER_AVAILABLE:
            logger.warning("Whisper não disponível para transcrição")
            return None
        
        if not self.is_loaded:
            loaded = await self.load_model()
            if not loaded:
                return None
        
        # Verificar se arquivo existe
        audio_file = Path(audio_path)
        if not audio_file.exists():
            logger.error(f"Arquivo de áudio não encontrado: {audio_path}")
            return None
        
        try:
            logger.info(f"Transcrevendo áudio: {audio_path}")
            
            # Mapear código de idioma para Whisper
            whisper_lang = None
            if language:
                # Extrair código base (pt-BR -> pt, en-US -> en)
                whisper_lang = language.split("-")[0].lower()
            
            # Executar transcrição em thread separada
            result = await asyncio.to_thread(
                self._transcribe_sync,
                str(audio_path),
                whisper_lang
            )
            
            if result and result.get("text"):
                text = result["text"].strip()
                detected_lang = result.get("language", "unknown")
                logger.info(f"Transcrição concluída ({detected_lang}): {text[:100]}...")
                return text
            
            return None
            
        except Exception as e:
            logger.error(f"Erro na transcrição: {e}")
            return None
    
    def _transcribe_sync(
        self,
        audio_path: str,
        language: Optional[str] = None
    ) -> dict:
        """
        Transcrição síncrona do áudio.
        
        Args:
            audio_path: Caminho do arquivo
            language: Código do idioma (opcional)
        
        Returns:
            dict: Resultado do Whisper com 'text' e 'language'
        """
        options = {
            "fp16": False,  # CPU não suporta fp16
            "verbose": False,
        }
        
        if language:
            options["language"] = language
        
        return self.model.transcribe(audio_path, **options)
    
    async def unload_model(self) -> None:
        """Descarrega o modelo para liberar memória."""
        if self.model is not None:
            del self.model
            self.model = None
        
        self.is_loaded = False
        logger.info("Modelo Whisper descarregado")


# Singleton do serviço
_transcription_service: Optional[TranscriptionService] = None


def get_transcription_service() -> TranscriptionService:
    """
    Retorna instância singleton do serviço de transcrição.
    
    Returns:
        TranscriptionService: Instância do serviço
    """
    global _transcription_service
    if _transcription_service is None:
        _transcription_service = TranscriptionService()
    return _transcription_service
