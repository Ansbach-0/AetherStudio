"""
Serviço de Text-to-Speech com F5-TTS.

Implementação real do voice cloning usando F5-TTS model.
Suporta clonagem zero-shot a partir de áudio de referência.
"""

import asyncio
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

# Configurar variáveis de ambiente ANTES de importar torch e transformers
from backend.config import get_settings
_settings = get_settings()

# Configurar HuggingFace cache para evitar re-download de modelos
# DEVE ser feito antes de importar transformers/torch
hf_cache_path = Path(_settings.hf_home).resolve()
hf_cache_path.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(hf_cache_path))
os.environ.setdefault("HF_HUB_CACHE", str(hf_cache_path / "hub"))
os.environ.setdefault("TRANSFORMERS_CACHE", str(hf_cache_path / "transformers"))

if _settings.use_rocm:
    os.environ["HSA_OVERRIDE_GFX_VERSION"] = _settings.hsa_override_gfx_version
    os.environ["ROCR_VISIBLE_DEVICES"] = _settings.rocm_visible_devices
    os.environ["HIP_VISIBLE_DEVICES"] = _settings.rocm_visible_devices
    os.environ["PYTORCH_ROCM_ARCH"] = _settings.pytorch_rocm_arch

from backend.utils.logger import get_logger

# Import PyTorch condicionalmente
try:
    import torch
    TORCH_AVAILABLE = True
    
    # IMPORTANTE: Monkey-patch do torchaudio.load para evitar torchcodec
    # O torchaudio 2.10+ usa torchcodec por padrão, que não está disponível no Windows/CPU
    # Forçamos o uso do backend soundfile que funciona universalmente
    try:
        import torchaudio
        import soundfile as sf
        
        # Guarda a função original
        _original_torchaudio_load = torchaudio.load
        
        def _patched_torchaudio_load(filepath, *args, **kwargs):
            """
            Wrapper que força uso do soundfile para carregar áudio.
            Evita erro do torchcodec no Windows/CPU.
            """
            try:
                # Tenta usar soundfile diretamente (mais confiável)
                data, sample_rate = sf.read(filepath, dtype='float32')
                # Converte para tensor PyTorch no formato esperado (channels, samples)
                if len(data.shape) == 1:
                    # Mono: adiciona dimensão de canal
                    waveform = torch.from_numpy(data).unsqueeze(0)
                else:
                    # Stereo/Multi-channel: transpõe para (channels, samples)
                    waveform = torch.from_numpy(data.T)
                return waveform, sample_rate
            except Exception:
                # Fallback para função original se soundfile falhar
                return _original_torchaudio_load(filepath, *args, **kwargs)
        
        # Aplica o monkey-patch
        torchaudio.load = _patched_torchaudio_load
        _TORCHAUDIO_PATCHED = True
        
    except ImportError:
        _TORCHAUDIO_PATCHED = False
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    _TORCHAUDIO_PATCHED = False

# Import scipy para salvar áudio (evita torchcodec do torchaudio)
try:
    import numpy as np
    from scipy.io import wavfile as scipy_wavfile
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    np = None
    scipy_wavfile = None

# Tentar importar DirectML se disponível
try:
    import torch_directml
    DIRECTML_AVAILABLE = True
except ImportError:
    DIRECTML_AVAILABLE = False
    torch_directml = None

# Import F5-TTS API simplificada condicionalmente
try:
    from f5_tts.api import F5TTS
    F5_TTS_AVAILABLE = True
except ImportError:
    F5_TTS_AVAILABLE = False
    F5TTS = None

# Import serviço de transcrição
from backend.services.transcription_service import get_transcription_service, WHISPER_AVAILABLE

logger = get_logger(__name__)
settings = get_settings()

# Log do status do monkey-patch do torchaudio
if TORCH_AVAILABLE and _TORCHAUDIO_PATCHED:
    logger.info("Monkey-patch do torchaudio.load aplicado com sucesso (usando soundfile)")
elif TORCH_AVAILABLE:
    logger.warning("Não foi possível aplicar monkey-patch do torchaudio - pode haver erros com torchcodec")


class TTSService:
    """
    Serviço de Text-to-Speech usando F5-TTS.
    
    Implementação usando a API simplificada do F5-TTS que:
    - Carrega modelo e vocoder automaticamente
    - Suporta clonagem zero-shot (6+ segundos de referência)
    - Múltiplos idiomas (PT, EN, ES)
    - Controle de velocidade
    
    Attributes:
        f5tts: Instância da API simplificada F5TTS
        model: Alias para f5tts (compatibilidade)
        device: Dispositivo (cuda/cpu)
        is_loaded: Status do modelo
    """
    
    # Configurações de modelo
    MODEL_NAME = "F5-TTS"
    SAMPLE_RATE = 24000
    HOP_LENGTH = 256
    TARGET_RMS = 0.1
    
    def __init__(self):
        """Inicializa o serviço TTS."""
        self.f5tts = None  # Instância da API simplificada
        self.model = None  # Alias para compatibilidade
        self.device = self._get_device()
        self.is_loaded = False
        
        logger.info(f"TTSService inicializado (device: {self.device})")
        if TORCH_AVAILABLE and settings.use_rocm:
            logger.info(f"ROCm configurado: HSA_GFX={settings.hsa_override_gfx_version}, ARCH={settings.pytorch_rocm_arch}")
    
    def _get_device(self) -> str:
        """
        Detecta melhor dispositivo disponível.
        
        Prioridade: CUDA/ROCm > DirectML > MPS > CPU
        """
        if not TORCH_AVAILABLE:
            return "cpu"
        
        # Verificar CUDA/ROCm
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "Unknown"
            logger.info(f"GPU detectada: {device_name}")
            is_rocm = hasattr(torch.version, 'hip') and torch.version.hip is not None
            if is_rocm:
                logger.info(f"Usando ROCm {torch.version.hip}")
            return settings.gpu_device
        
        # Verificar DirectML (WSL com GPU AMD)
        if DIRECTML_AVAILABLE and settings.use_directml:
            try:
                dml = torch_directml.device(settings.directml_device_id)
                logger.info(f"Usando DirectML: {dml}")
                return str(dml)
            except Exception as e:
                logger.warning(f"DirectML falhou: {e}")
        
        # Fallback MPS (Mac)
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        
        return "cpu"
    
    async def load_model(self) -> bool:
        """
        Carrega modelo F5-TTS e vocoder.
        
        Returns:
            bool: True se carregado com sucesso
        """
        if self.is_loaded:
            return True
        
        if not F5_TTS_AVAILABLE or not TORCH_AVAILABLE:
            error_msg = (
                "F5-TTS ou PyTorch não instalado. "
                f"F5_TTS_AVAILABLE={F5_TTS_AVAILABLE}, TORCH_AVAILABLE={TORCH_AVAILABLE}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            logger.info("Carregando modelo F5-TTS...")
            # Executar carregamento em thread separada
            await asyncio.to_thread(self._load_model_sync)
            self.is_loaded = True
            logger.info(f"F5-TTS carregado com sucesso no dispositivo: {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar F5-TTS: {e}")
            raise
    
    def _load_model_sync(self) -> None:
        """
        Carregamento síncrono do modelo usando API simplificada F5TTS.
        
        A API simplificada carrega modelo e vocoder automaticamente.
        """
        # Determinar device para o modelo
        model_device = self.device
        if self.device.startswith("privateuseone"):
            # F5-TTS não suporta DirectML nativamente
            logger.info("F5-TTS não suporta DirectML, usando CPU para modelo")
            model_device = "cpu"
        
        # Criar instância da API simplificada
        # O modelo e vocoder são carregados automaticamente
        self.f5tts = F5TTS(device=model_device)
        
        # Alias para compatibilidade com código existente (ex: voice_pipeline)
        self.model = self.f5tts
        
        logger.info(f"F5TTS API carregada no device: {model_device}")
    
    async def unload_model(self) -> None:
        """Descarrega modelo para liberar memória."""
        if self.f5tts is not None:
            del self.f5tts
            self.f5tts = None
            self.model = None  # Limpar alias também
        
        # Forçar garbage collection antes de limpar cache GPU
        import gc
        gc.collect()
        
        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.is_loaded = False
        logger.info("Modelo TTS descarregado")
    
    async def synthesize(
        self,
        text: str,
        reference_audio: str,
        language: str = "pt-BR",
        speed: float = 1.0,
        reference_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sintetiza texto com voz clonada.
        
        Args:
            text: Texto para sintetizar
            reference_audio: Caminho do áudio de referência
            language: Código do idioma
            speed: Velocidade da fala (0.5-2.0)
            reference_text: Transcrição do áudio de referência (se None, usa fallback)
        
        Returns:
            Dict com audio_url, duration, sample_rate
        """
        if not self.is_loaded:
            await self.load_model()
        
        # Gerar ID do arquivo de saída
        file_id = str(uuid.uuid4())
        output_dir = Path(settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{file_id}.wav"
        
        # Se modelo não está disponível, lançar erro
        if self.model is None or not F5_TTS_AVAILABLE or not TORCH_AVAILABLE:
            error_msg = f"Modelo TTS não disponível: model={self.model is not None}, F5_TTS={F5_TTS_AVAILABLE}, TORCH={TORCH_AVAILABLE}"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        try:
            # Executar síntese em thread separada (operação bloqueante)
            result = await asyncio.to_thread(
                self._synthesize_sync,
                text,
                reference_audio,
                str(output_path),
                speed,
                reference_text,
                language  # Passa idioma para ajudar na transcrição automática
            )
            
            return {
                "audio_url": f"/outputs/{file_id}.wav",
                "duration": result["duration"],
                "sample_rate": self.SAMPLE_RATE,
                "format": "wav"
            }
            
        except Exception as e:
            import traceback
            logger.error(f"Erro na síntese: {e}")
            logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            raise
    
    def _synthesize_sync(
        self,
        text: str,
        reference_audio: str,
        output_path: str,
        speed: float,
        reference_text: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Síntese síncrona usando API simplificada F5TTS.
        
        Args:
            text: Texto para sintetizar (gen_text)
            reference_audio: Caminho do áudio de referência (ref_file)
            output_path: Caminho de saída (file_wave)
            speed: Velocidade da fala
            reference_text: Transcrição do áudio de referência (ref_text)
            language: Idioma para transcrição automática
        
        Returns:
            Dict com informações do áudio gerado
        """
        # IMPORTANTE: F5-TTS REQUER que ref_text corresponda exatamente ao áudio
        # Se não fornecido, usamos Whisper para transcrever automaticamente
        ref_text_input = None
        
        if reference_text and reference_text.strip():
            ref_text_input = reference_text.strip()
            logger.info(f"Usando reference_text fornecido: {ref_text_input[:50]}...")
        else:
            # Tentar transcrição automática com Whisper
            if WHISPER_AVAILABLE:
                try:
                    import asyncio
                    transcription_service = get_transcription_service()
                    # Executar transcrição de forma síncrona
                    loop = asyncio.new_event_loop()
                    try:
                        ref_text_input = loop.run_until_complete(
                            transcription_service.transcribe(reference_audio, language)
                        )
                    finally:
                        loop.close()
                    
                    if ref_text_input:
                        logger.info(f"Transcrição automática: {ref_text_input[:50]}...")
                    else:
                        logger.warning("Transcrição automática retornou vazio")
                except Exception as e:
                    logger.warning(f"Erro na transcrição automática: {e}")
            
            # Fallback se transcrição falhar
            if not ref_text_input:
                # Usar texto genérico como último recurso
                # AVISO: Isso pode resultar em áudio de baixa qualidade
                ref_text_input = "Sample audio for voice cloning reference."
                logger.warning(
                    "AVISO: Usando texto genérico como fallback. "
                    "Para melhor qualidade, forneça a transcrição do áudio de referência!"
                )
        
        # Usar API simplificada do F5-TTS
        # Retorna: (wav_array, sample_rate, spectrogram)
        try:
            wav, sr, _ = self.f5tts.infer(
                ref_file=reference_audio,
                ref_text=ref_text_input,
                gen_text=text,
                file_wave=output_path,  # Salva automaticamente
                speed=speed,
                seed=None,  # Geração aleatória
            )
            
            # Calcular duração do áudio gerado
            duration = len(wav) / sr
            logger.info(f"Síntese concluída: {duration:.2f}s, {output_path}")
            
            return {
                "duration": duration,
                "sample_rate": sr
            }
            
        except Exception as e:
            # Se file_wave falhar, tentar salvar manualmente como backup
            logger.warning(f"Erro no file_wave automático, tentando backup: {e}")
            
            wav, sr, _ = self.f5tts.infer(
                ref_file=reference_audio,
                ref_text=ref_text_input,
                gen_text=text,
                file_wave=None,  # Não salvar automaticamente
                speed=speed,
                seed=None,
            )
            
            # Salvar áudio usando scipy (evita torchcodec do torchaudio)
            if SCIPY_AVAILABLE:
                # Converter para int16 para WAV
                audio_np = np.array(wav)
                # Normalizar para range int16
                audio_int16 = (audio_np * 32767).astype(np.int16)
                scipy_wavfile.write(output_path, sr, audio_int16)
            else:
                # Fallback para wave module (stdlib)
                import wave
                audio_list = [int(s * 32767) for s in wav]
                with wave.open(output_path, 'w') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)  # 16-bit
                    wav_file.setframerate(sr)
                    wav_file.writeframes(bytes(b''.join(s.to_bytes(2, 'little', signed=True) for s in audio_list)))
            
            duration = len(wav) / sr
            logger.info(f"Síntese concluída (backup): {duration:.2f}s, {output_path}")
            
            return {
                "duration": duration,
                "sample_rate": sr
            }
    
    async def _mock_synthesize(
        self,
        text: str,
        output_path: Path,
        speed: float
    ) -> Dict[str, Any]:
        """
        Síntese mock quando modelo não disponível.
        
        Cria arquivo de áudio silencioso com duração estimada.
        """
        # Estimar duração: ~150 palavras/min, ajustado por velocidade
        words = len(text.split())
        duration = (words / 150) * 60 / speed
        duration = max(1.0, min(duration, 300.0))
        
        # Criar áudio silencioso (para testes)
        if SCIPY_AVAILABLE:
            samples = int(duration * self.SAMPLE_RATE)
            silence = np.zeros(samples, dtype=np.int16)
            scipy_wavfile.write(str(output_path), self.SAMPLE_RATE, silence)
        else:
            # Fallback: criar arquivo WAV vazio usando wave (stdlib)
            import wave
            samples = int(duration * self.SAMPLE_RATE)
            with wave.open(str(output_path), 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.SAMPLE_RATE)
                # Escreve silêncio (zeros) - 16-bit silence (2 bytes per sample)
                silence_data = bytes(samples * 2)
                wav_file.writeframes(silence_data)
        
        logger.warning(f"Mock synthesis: {duration:.2f}s (modelo não disponível)")
        
        return {
            "audio_url": f"/outputs/{output_path.name}",
            "duration": duration,
            "sample_rate": self.SAMPLE_RATE,
            "format": "wav",
            "mock": True
        }
    
    async def get_supported_languages(self) -> list:
        """
        Retorna lista de idiomas suportados.
        
        Returns:
            list: Códigos de idioma suportados
        """
        return settings.allowed_languages
    
    @property
    def status(self) -> Dict[str, Any]:
        """Retorna status do serviço."""
        return {
            "loaded": self.is_loaded,
            "model": self.model,  # Alias para f5tts (compatibilidade com voice_pipeline)
            "f5tts": self.f5tts,  # Instância real da API
            "model_available": self.f5tts is not None,
            "mock_mode": self.f5tts is None,  # Indica se está em modo mock
            "torch_available": TORCH_AVAILABLE,
            "f5_tts_installed": F5_TTS_AVAILABLE,
            "device": self.device,
            "model_type": "F5-TTS (API simplificada)",
            "sample_rate": self.SAMPLE_RATE
        }
