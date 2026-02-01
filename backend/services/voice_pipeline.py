"""
Pipeline híbrido para voice cloning com estilo emocional.

Combina F5-TTS (texto → fala) com RVC (estilo/timbre) para
criar um sistema completo de geração de voz personalizada.
"""

import asyncio
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import get_settings
from backend.utils.logger import get_logger
from backend.services.tts_service import TTSService
from backend.services.rvc_service import RVCService
from backend.services.language_detector import get_language_detector

logger = get_logger(__name__)
settings = get_settings()


class VoicePipeline:
    """
    Pipeline de processamento de voz.
    
    Combina múltiplos serviços para criar fluxos flexíveis
    de geração e transformação de voz.
    
    Fluxos suportados:
    1. TTS only: Texto → Áudio (voz clonada com F5-TTS)
    2. RVC only: Áudio → Áudio (conversão de timbre)
    3. TTS + RVC: Texto → Áudio → Áudio estilizado
    
    Attributes:
        tts: Serviço de Text-to-Speech
        rvc: Serviço de conversão de voz
        language_detector: Detector automático de idioma
    """
    
    # Emoções suportadas e seus ajustes
    EMOTION_PRESETS = {
        "neutral": {"pitch_shift": 0, "speed": 1.0},
        "happy": {"pitch_shift": 2, "speed": 1.1},
        "sad": {"pitch_shift": -2, "speed": 0.9},
        "angry": {"pitch_shift": 1, "speed": 1.2},
        "calm": {"pitch_shift": -1, "speed": 0.85},
        "excited": {"pitch_shift": 3, "speed": 1.15},
        "whisper": {"pitch_shift": 0, "speed": 0.8},
        "serious": {"pitch_shift": -1, "speed": 0.95},
    }
    
    def __init__(
        self,
        tts_service: Optional[TTSService] = None,
        rvc_service: Optional[RVCService] = None
    ):
        """
        Inicializa o pipeline de voz.
        
        Args:
            tts_service: Serviço TTS (cria novo se None)
            rvc_service: Serviço RVC (cria novo se None)
        """
        self.tts = tts_service or TTSService()
        self.rvc = rvc_service or RVCService()
        self.language_detector = get_language_detector()
        
        logger.info("VoicePipeline inicializado")
    
    async def initialize(self) -> bool:
        """
        Inicializa todos os serviços do pipeline.
        
        Returns:
            bool: True se todos os serviços foram inicializados
        """
        try:
            # Carregar modelos em paralelo
            tts_loaded, rvc_loaded = await asyncio.gather(
                self.tts.load_model(),
                self.rvc.load_model(),
                return_exceptions=True
            )
            
            # Verificar resultados
            tts_ok = tts_loaded is True
            rvc_ok = rvc_loaded is True
            
            if not tts_ok:
                logger.warning(f"TTS não carregou completamente: {tts_loaded}")
            
            if not rvc_ok:
                logger.warning(f"RVC não carregou completamente: {rvc_loaded}")
            
            return tts_ok or rvc_ok  # Pelo menos um deve funcionar
            
        except Exception as e:
            logger.error(f"Erro ao inicializar pipeline: {e}")
            return False
    
    async def text_to_speech(
        self,
        text: str,
        reference_audio: str,
        language: Optional[str] = None,
        speed: float = 1.0,
        reference_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Converte texto em fala usando voz de referência.
        
        Usa F5-TTS para síntese de voz clonada.
        
        Args:
            text: Texto para sintetizar
            reference_audio: Caminho do áudio de referência
            language: Código de idioma (auto-detecta se None)
            speed: Velocidade da fala (0.5-2.0)
            reference_text: Transcrição do áudio de referência (evita Whisper/TorchCodec)
        
        Returns:
            Dict com audio_url, duration, sample_rate, etc.
        """
        # Auto-detectar idioma se não especificado
        if not language:
            language = self.language_detector.detect(text)
            logger.info(f"Idioma auto-detectado: {language}")
        
        # Executar TTS
        result = await self.tts.synthesize(
            text=text,
            reference_audio=reference_audio,
            language=language,
            speed=speed,
            reference_text=reference_text
        )
        
        result["detected_language"] = language
        result["pipeline_stage"] = "tts"
        
        return result
    
    async def voice_conversion(
        self,
        input_audio: str,
        voice_model: str,
        pitch_shift: int = 0,
        index_rate: float = 0.75
    ) -> Dict[str, Any]:
        """
        Converte voz de áudio existente para voz alvo.
        
        Usa RVC para conversão de timbre mantendo conteúdo.
        
        Args:
            input_audio: Caminho do áudio de entrada
            voice_model: Caminho do modelo de voz alvo
            pitch_shift: Ajuste de tom (-12 a +12)
            index_rate: Taxa de uso do índice FAISS (0-1)
        
        Returns:
            Dict com audio_url, duration, etc.
        """
        result = await self.rvc.convert(
            input_audio_path=input_audio,
            voice_model=voice_model,
            pitch_shift=pitch_shift,
            index_rate=index_rate
        )
        
        result["pipeline_stage"] = "rvc"
        
        return result
    
    async def text_to_speech_styled(
        self,
        text: str,
        reference_audio: str,
        style_model: Optional[str] = None,
        emotion: str = "neutral",
        language: Optional[str] = None,
        speed: Optional[float] = None,
        pitch_shift: Optional[int] = None,
        apply_rvc: bool = True,
        reference_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gera fala com estilo emocional.
        
        Pipeline completo:
        1. Detecta idioma automaticamente (se não especificado)
        2. Sintetiza texto com F5-TTS usando referência
        3. Aplica estilo emocional com RVC (se solicitado)
        
        Args:
            text: Texto para sintetizar
            reference_audio: Áudio de referência para clonagem
            style_model: Modelo RVC para estilização (opcional)
            emotion: Estilo emocional (neutral, happy, sad, etc.)
            language: Código de idioma (auto-detecta se None)
            speed: Velocidade (usa preset de emoção se None)
            pitch_shift: Pitch shift (usa preset de emoção se None)
            apply_rvc: Se deve aplicar RVC após TTS
            reference_text: Transcrição do áudio de referência (evita Whisper/TorchCodec)
        
        Returns:
            Dict com resultado completo do pipeline
        """
        pipeline_id = str(uuid.uuid4())[:8]
        logger.info(f"[{pipeline_id}] Iniciando pipeline TTS+RVC")
        
        # Obter configurações de emoção
        emotion_preset = self.EMOTION_PRESETS.get(
            emotion.lower(),
            self.EMOTION_PRESETS["neutral"]
        )
        
        # Usar valores fornecidos ou do preset
        actual_speed = speed if speed is not None else emotion_preset["speed"]
        actual_pitch = pitch_shift if pitch_shift is not None else emotion_preset["pitch_shift"]
        
        # Auto-detectar idioma
        if not language:
            language = self.language_detector.detect(text)
            logger.info(f"[{pipeline_id}] Idioma detectado: {language}")
        
        # Etapa 1: TTS com F5-TTS
        logger.info(f"[{pipeline_id}] Etapa 1: Síntese TTS")
        tts_result = await self.tts.synthesize(
            text=text,
            reference_audio=reference_audio,
            language=language,
            speed=actual_speed,
            reference_text=reference_text
        )
        
        # Se não deve aplicar RVC ou não há modelo de estilo
        if not apply_rvc or not style_model:
            return {
                "pipeline_id": pipeline_id,
                "audio_url": tts_result["audio_url"],
                "duration": tts_result["duration"],
                "sample_rate": tts_result["sample_rate"],
                "format": tts_result.get("format", "wav"),
                "language": language,
                "emotion": emotion,
                "speed": actual_speed,
                "stages_completed": ["tts"],
                "mock": tts_result.get("mock", False)
            }
        
        # Etapa 2: Estilização com RVC
        logger.info(f"[{pipeline_id}] Etapa 2: Estilização RVC")
        
        # Converter URL para caminho de arquivo
        tts_audio_path = self._url_to_path(tts_result["audio_url"])
        
        rvc_result = await self.rvc.convert(
            input_audio_path=tts_audio_path,
            voice_model=style_model,
            pitch_shift=actual_pitch
        )
        
        logger.info(f"[{pipeline_id}] Pipeline concluído")
        
        return {
            "pipeline_id": pipeline_id,
            "audio_url": rvc_result["audio_url"],
            "duration": rvc_result["duration"],
            "sample_rate": rvc_result["sample_rate"],
            "format": rvc_result.get("format", "wav"),
            "language": language,
            "emotion": emotion,
            "speed": actual_speed,
            "pitch_shift": actual_pitch,
            "stages_completed": ["tts", "rvc"],
            "intermediate_audio": tts_result["audio_url"],
            "mock": tts_result.get("mock", False) or rvc_result.get("mock", False)
        }
    
    async def batch_synthesize(
        self,
        items: List[Dict[str, Any]],
        reference_audio: str,
        style_model: Optional[str] = None,
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Processa múltiplos textos em lote.
        
        Útil para gerar múltiplos áudios de forma eficiente.
        
        Args:
            items: Lista de dicts com 'text' e opcionalmente 'emotion'
            reference_audio: Áudio de referência para todos
            style_model: Modelo de estilo opcional
            max_concurrent: Número máximo de processamentos paralelos
        
        Returns:
            List[Dict]: Resultados para cada item
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_item(item: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                try:
                    text = item.get("text", "")
                    emotion = item.get("emotion", "neutral")
                    
                    result = await self.text_to_speech_styled(
                        text=text,
                        reference_audio=reference_audio,
                        style_model=style_model,
                        emotion=emotion
                    )
                    
                    return {"success": True, "result": result}
                    
                except Exception as e:
                    logger.error(f"Erro no batch item: {e}")
                    return {"success": False, "error": str(e)}
        
        # Processar todos os itens
        tasks = [process_item(item) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Converter exceções em resultados de erro
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append({
                    "success": False,
                    "error": str(result),
                    "index": i
                })
            else:
                result["index"] = i
                final_results.append(result)
        
        return final_results
    
    def _url_to_path(self, url: str) -> str:
        """
        Converte URL de saída para caminho de arquivo.
        
        Args:
            url: URL no formato /outputs/xxx.wav
        
        Returns:
            str: Caminho absoluto do arquivo
        """
        if url.startswith("/outputs/"):
            filename = url.replace("/outputs/", "")
            return str(Path(settings.output_dir) / filename)
        
        return url
    
    def get_available_emotions(self) -> List[Dict[str, Any]]:
        """
        Retorna lista de emoções disponíveis com seus presets.
        
        Returns:
            List[Dict]: Informações sobre cada emoção
        """
        return [
            {
                "name": emotion,
                "pitch_shift": preset["pitch_shift"],
                "speed": preset["speed"]
            }
            for emotion, preset in self.EMOTION_PRESETS.items()
        ]
    
    @property
    def status(self) -> Dict[str, Any]:
        """
        Retorna status completo do pipeline.
        
        Indica claramente se está em modo mock/desenvolvimento.
        """
        tts_status = self.tts.status
        rvc_status = self.rvc.status
        
        # Determinar o modo de operação
        tts_real = tts_status.get("model") is not None and not tts_status.get("mock_mode", True)
        rvc_real = rvc_status.get("model") is not None and not rvc_status.get("mock_mode", True)
        
        if tts_real and rvc_real:
            mode = "full"  # Todos os modelos carregados
        elif tts_real or rvc_real:
            mode = "partial"  # Apenas um modelo carregado
        else:
            mode = "mock"  # Nenhum modelo real carregado
        
        return {
            "tts": tts_status,
            "rvc": rvc_status,
            "language_detector": self.language_detector.status,
            "available_emotions": list(self.EMOTION_PRESETS.keys()),
            "ready": self.tts.is_loaded or self.rvc.is_loaded,
            "mode": mode,  # "full", "partial", ou "mock"
            "mock_mode": mode == "mock",
        }


# Instância singleton do pipeline
_pipeline_instance: Optional[VoicePipeline] = None


def get_voice_pipeline() -> VoicePipeline:
    """
    Retorna instância singleton do pipeline de voz.
    
    Returns:
        VoicePipeline: Instância do pipeline
    """
    global _pipeline_instance
    
    if _pipeline_instance is None:
        _pipeline_instance = VoicePipeline()
    
    return _pipeline_instance


async def initialize_pipeline() -> VoicePipeline:
    """
    Inicializa e retorna o pipeline de voz.
    
    Carrega todos os modelos necessários.
    
    Returns:
        VoicePipeline: Pipeline inicializado
    """
    pipeline = get_voice_pipeline()
    await pipeline.initialize()
    return pipeline
