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

# Configurar variáveis de ambiente ROCm ANTES de importar torch
from backend.config import get_settings
_settings = get_settings()
if _settings.use_rocm:
    os.environ["HSA_OVERRIDE_GFX_VERSION"] = _settings.hsa_override_gfx_version
    os.environ["ROCR_VISIBLE_DEVICES"] = _settings.rocm_visible_devices
    os.environ["HIP_VISIBLE_DEVICES"] = _settings.rocm_visible_devices
    os.environ["PYTORCH_ROCM_ARCH"] = _settings.pytorch_rocm_arch

from backend.utils.logger import get_logger

# Import PyTorch condicionalmente
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    torchaudio = None

# Tentar importar DirectML se disponível
try:
    import torch_directml
    DIRECTML_AVAILABLE = True
except ImportError:
    DIRECTML_AVAILABLE = False
    torch_directml = None

# Import F5-TTS modules condicionalmente para evitar erros se não instalado
try:
    from f5_tts.model import DiT
    from f5_tts.infer.utils_infer import (
        load_vocoder,
        load_model,
        infer_process,
        preprocess_ref_audio_text
    )
    F5_TTS_AVAILABLE = True
except ImportError:
    F5_TTS_AVAILABLE = False

logger = get_logger(__name__)
settings = get_settings()


class TTSService:
    """
    Serviço de Text-to-Speech usando F5-TTS.
    
    Implementação real de voice cloning com suporte a:
    - Clonagem zero-shot (6+ segundos de referência)
    - Múltiplos idiomas (PT, EN, ES)
    - Controle de velocidade
    - Batch processing
    
    Attributes:
        model: Modelo F5-TTS carregado
        vocoder: Vocoder para síntese de áudio
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
        self.model = None
        self.vocoder = None
        self.device = self._get_device()
        self._model_device = self.device  # Device real usado pelo modelo F5-TTS
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
            logger.warning("F5-TTS ou PyTorch não instalado. Usando modo mock.")
            self.is_loaded = True  # Permite operar em modo mock
            return True
        
        try:
            logger.info("Carregando modelo F5-TTS...")
            # Executar carregamento em thread separada
            await asyncio.to_thread(self._load_model_sync)
            self.is_loaded = True
            logger.info(f"F5-TTS carregado com sucesso no dispositivo: {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar F5-TTS: {e}")
            logger.warning("Operando em modo mock.")
            self.is_loaded = True
            return True
    
    def _load_model_sync(self) -> None:
        """Carregamento síncrono do modelo (executado em thread)."""
        base_dir = Path(settings.models_dir) / "f5-tts" / "F5TTS_Base"
        pt_ckpt = base_dir / "model_1200000.pt"
        st_ckpt = base_dir / "model_1200000.safetensors"
        ckpt_path = str(pt_ckpt) if pt_ckpt.exists() else (str(st_ckpt) if st_ckpt.exists() else "")
        vocab_path = str(base_dir / "vocab.txt")
        
        # F5-TTS não suporta DirectML nativamente - usar CPU para carregamento
        # e converter para device alvo depois se necessário
        model_device = self.device
        if self.device.startswith("privateuseone"):
            logger.info("F5-TTS não suporta DirectML, usando CPU para modelo")
            model_device = "cpu"
        
        self.model = load_model(
            model_cls=DiT,
            model_cfg=dict(dim=1024, depth=22, heads=16, ff_mult=2, text_dim=512, conv_layers=4),
            ckpt_path=ckpt_path,
            mel_spec_type="vocos",
            vocab_file=vocab_path if Path(vocab_path).exists() else "",
            device=model_device
        )
        
        # Armazenar device real do modelo para inferência
        self._model_device = model_device
        
        self.vocoder = load_vocoder(is_local=False, local_path="", device=model_device)
    
    async def unload_model(self) -> None:
        """Descarrega modelo para liberar memória."""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.vocoder is not None:
            del self.vocoder
            self.vocoder = None
        
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
        speed: float = 1.0
    ) -> Dict[str, Any]:
        """
        Sintetiza texto com voz clonada.
        
        Args:
            text: Texto para sintetizar
            reference_audio: Caminho do áudio de referência
            language: Código do idioma
            speed: Velocidade da fala (0.5-2.0)
        
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
        
        # Se modelo não está disponível, usar mock
        if self.model is None or not F5_TTS_AVAILABLE or not TORCH_AVAILABLE:
            return await self._mock_synthesize(text, output_path, speed)
        
        try:
            # Executar síntese em thread separada (operação bloqueante)
            result = await asyncio.to_thread(
                self._synthesize_sync,
                text,
                reference_audio,
                str(output_path),
                speed
            )
            
            return {
                "audio_url": f"/outputs/{file_id}.wav",
                "duration": result["duration"],
                "sample_rate": self.SAMPLE_RATE,
                "format": "wav"
            }
            
        except Exception as e:
            logger.error(f"Erro na síntese: {e}")
            return await self._mock_synthesize(text, output_path, speed)
    
    def _synthesize_sync(
        self,
        text: str,
        reference_audio: str,
        output_path: str,
        speed: float
    ) -> Dict[str, Any]:
        """
        Síntese síncrona (executada em thread pool).
        
        Args:
            text: Texto para sintetizar
            reference_audio: Caminho do áudio de referência
            output_path: Caminho de saída
            speed: Velocidade
        
        Returns:
            Dict com informações do áudio gerado
        """
        # Processar áudio de referência (não aceita device)
        ref_audio, ref_text = preprocess_ref_audio_text(
            reference_audio,
            ""  # Transcrição vazia = auto-detectar
        )
        
        # Executar inferência (usar _model_device para F5-TTS)
        generated_audio, final_sample_rate, _ = infer_process(
            ref_audio,
            ref_text,
            text,
            self.model,
            self.vocoder,
            mel_spec_type="vocos",
            speed=speed,
            device=self._model_device
        )
        
        # Salvar áudio
        torchaudio.save(
            output_path,
            torch.tensor(generated_audio).unsqueeze(0),
            final_sample_rate
        )
        
        duration = len(generated_audio) / final_sample_rate
        
        logger.info(f"Síntese concluída: {duration:.2f}s, {output_path}")
        
        return {
            "duration": duration,
            "sample_rate": final_sample_rate
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
        if TORCH_AVAILABLE:
            samples = int(duration * self.SAMPLE_RATE)
            silence = torch.zeros(1, samples)
            torchaudio.save(str(output_path), silence, self.SAMPLE_RATE)
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
            "model_available": self.model is not None,
            "torch_available": TORCH_AVAILABLE,
            "f5_tts_installed": F5_TTS_AVAILABLE,
            "device": self.device,
            "model_type": "F5-TTS",
            "sample_rate": self.SAMPLE_RATE
        }
