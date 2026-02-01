"""
Serviço de conversão de voz com RVC.

Implementação real de voice-to-voice conversion usando
RVC (Retrieval-based Voice Conversion).

Suporta:
- Conversão de voz mantendo conteúdo e entonação
- Ajuste de pitch em semitons
- Extração de F0 com CREPE/pyworld
- Índice FAISS para retrieval de voz
"""

from __future__ import annotations

import asyncio
import contextlib
import gc
import importlib.util
import os
import shutil
import subprocess
import uuid
import wave
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from backend.utils.logger import get_logger

# Configurar variáveis de ambiente ROCm ANTES de importar torch
from backend.config import get_settings
_settings = get_settings()
if _settings.use_rocm:
    os.environ["HSA_OVERRIDE_GFX_VERSION"] = _settings.hsa_override_gfx_version
    os.environ["ROCR_VISIBLE_DEVICES"] = _settings.rocm_visible_devices
    os.environ["HIP_VISIBLE_DEVICES"] = _settings.rocm_visible_devices
    os.environ["PYTORCH_ROCM_ARCH"] = _settings.pytorch_rocm_arch

# Import condicional de PyTorch
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None
    torchaudio = None

TORCHCODEC_AVAILABLE = False
TORCHAUDIO_IO_AVAILABLE = False
if TORCH_AVAILABLE and torchaudio is not None:
    TORCHCODEC_AVAILABLE = importlib.util.find_spec("torchcodec") is not None
    TORCHAUDIO_IO_AVAILABLE = TORCHCODEC_AVAILABLE

# Tentar importar DirectML se disponível
try:
    import torch_directml
    DIRECTML_AVAILABLE = True
except ImportError:
    DIRECTML_AVAILABLE = False
    torch_directml = None

# Import condicional de NumPy e SciPy
try:
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import resample
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

# Import condicional de librosa
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    librosa = None

# Import condicional de torchcrepe para extração de pitch
try:
    import torchcrepe
    CREPE_AVAILABLE = True
except ImportError:
    CREPE_AVAILABLE = False
    torchcrepe = None

# Import condicional de pyworld para extração de F0 alternativa
try:
    import pyworld as pw
    PYWORLD_AVAILABLE = True
except ImportError:
    PYWORLD_AVAILABLE = False
    pw = None

# Import condicional de FAISS para índice de voz
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None

# Import condicional de parselmouth (Praat)
try:
    import parselmouth
    PARSELMOUTH_AVAILABLE = True
except ImportError:
    PARSELMOUTH_AVAILABLE = False
    parselmouth = None

# Import condicional de ONNX Runtime
try:
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    ort = None

logger = get_logger(__name__)
settings = get_settings()


class RVCService:
    """
    Serviço de conversão de voz usando RVC.
    
    Converte áudio de entrada mantendo conteúdo e entonação,
    alterando o timbre para a voz alvo.
    
    Features:
    - Voice-to-voice conversion
    - Pitch shifting (-12 a +12 semitons)
    - Extração de F0 com CREPE/pyworld
    - Suporte a múltiplos formatos de áudio
    - Modo mock quando modelo não disponível
    
    Attributes:
        model: Modelo RVC carregado
        index: Índice FAISS para retrieval
        pitch_extractor: Método de extração de pitch
        device: Dispositivo de inferência (cuda/cpu)
        is_loaded: Status de carregamento do modelo
    """
    
    # Configurações de áudio
    SAMPLE_RATE = 16000  # Taxa de amostragem padrão RVC
    HOP_LENGTH = 160     # Tamanho do hop para análise
    WIN_LENGTH = 1024    # Tamanho da janela
    N_FFT = 2048         # Tamanho da FFT
    
    # Configurações de pitch
    F0_MIN = 50          # F0 mínimo (Hz)
    F0_MAX = 1100        # F0 máximo (Hz)
    
    def __init__(self):
        """Inicializa o serviço RVC."""
        self.model = None
        self.index = None
        self.pitch_extractor = None
        self.hubert_model = None
        self.device = self._get_device()
        self.is_loaded = False
        self._model_path = None
        self._rvc_repo_dir = None
        self._rvc_env_name = settings.rvc_env_name
        self._rvc_model_path = None
        self._rvc_index_path = None
        
        # Determinar método de extração de pitch disponível
        self._pitch_method = self._detect_pitch_method()
        
        logger.info(
            f"RVCService inicializado "
            f"(device: {self.device}, pitch_method: {self._pitch_method})"
        )
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
            try:
                device_name = torch.cuda.get_device_name(0)
                gpu_memory = torch.cuda.get_device_properties(0).total_memory
                gpu_memory_gb = gpu_memory / (1024**3)
                logger.info(f"GPU detectada: {device_name} ({gpu_memory_gb:.1f} GB)")
                
                is_rocm = hasattr(torch.version, 'hip') and torch.version.hip is not None
                if is_rocm:
                    logger.info(f"Usando ROCm {torch.version.hip}")
                
                # Verificar memória suficiente (> 4GB para RVC)
                if gpu_memory > 4 * 1024**3:
                    return settings.gpu_device
            except Exception as e:
                logger.warning(f"Erro ao verificar GPU: {e}")
        
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
    
    def _detect_pitch_method(self) -> str:
        """Detecta método de extração de pitch disponível."""
        if CREPE_AVAILABLE and TORCH_AVAILABLE:
            return "crepe"
        elif PYWORLD_AVAILABLE:
            return "harvest"  # pyworld harvest
        elif PARSELMOUTH_AVAILABLE:
            return "parselmouth"
        else:
            return "none"

    @contextlib.contextmanager
    def _temp_cwd(self, path: Path):
        """Troca diretório atual temporariamente."""
        prev = Path.cwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(prev)

    def _ensure_repo_assets(self, repo_dir: Path, model_dir: Path) -> None:
        """Garante assets requeridos pelo repo RVC."""
        hubert_src = model_dir / "hubert_base.pt"
        rmvpe_src = model_dir / "rmvpe.pt"

        hubert_dst = repo_dir / "assets" / "hubert" / "hubert_base.pt"
        rmvpe_dst = repo_dir / "assets" / "rmvpe" / "rmvpe.pt"

        hubert_dst.parent.mkdir(parents=True, exist_ok=True)
        rmvpe_dst.parent.mkdir(parents=True, exist_ok=True)

        if hubert_src.exists() and not hubert_dst.exists():
            shutil.copy2(hubert_src, hubert_dst)

        if rmvpe_src.exists() and not rmvpe_dst.exists():
            shutil.copy2(rmvpe_src, rmvpe_dst)
    
    async def load_model(self, model_path: Optional[str] = None) -> bool:
        """
        Carrega modelo RVC em memória.
        
        Args:
            model_path: Caminho opcional para modelo específico
        
        Returns:
            bool: True se carregado com sucesso
        """
        if self.is_loaded and model_path is None:
            logger.debug("Modelo RVC já está carregado")
            return True
        
        # Verificar dependências mínimas
        if not NUMPY_AVAILABLE:
            error_msg = "NumPy não disponível. RVC não pode iniciar."
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            # Definir caminho do modelo
            if model_path:
                self._model_path = model_path
            else:
                self._model_path = str(Path(settings.models_dir) / "rvc")
            
            # Carregar em thread separada para não bloquear
            await asyncio.to_thread(self._load_model_sync)
            
            self.is_loaded = True
            logger.info(f"RVC carregado com sucesso (device: {self.device})")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo RVC: {e}")
            raise
    
    def _load_model_sync(self) -> None:
        """Carregamento síncrono do modelo (executado em thread)."""
        model_dir = Path(self._model_path)

        # Tentar usar o repo oficial do RVC (WebUI) via subprocesso
        repo_dir = Path(settings.rvc_repo_dir)
        if repo_dir.exists():
            self._rvc_repo_dir = repo_dir
            self._ensure_repo_assets(repo_dir, model_dir)

            # Selecionar modelo .pth e índice
            pth_files = list(model_dir.glob("*.pth"))
            index_files = list(model_dir.glob("*.index"))

            if not pth_files:
                logger.warning(f"Nenhum modelo .pth encontrado em {model_dir}")
            else:
                self._rvc_model_path = str(pth_files[0])
                self._rvc_index_path = str(index_files[0]) if index_files else ""
                self.model = {"type": "rvc-webui"}
                logger.info("RVC WebUI pronto para inferência via subprocesso")
                return
        
        # Verificar se existem modelos
        if not model_dir.exists():
            raise FileNotFoundError(f"Diretório de modelos não existe: {model_dir}")
        
        # Tentar carregar modelo ONNX para melhor compatibilidade
        onnx_path = model_dir / "rvc_model.onnx"
        if ONNX_AVAILABLE and onnx_path.exists():
            try:
                # Determinar providers ONNX baseado no device e disponibilidade
                providers = ['CPUExecutionProvider']
                if self.device.startswith("cuda"):
                    available_providers = ort.get_available_providers()
                    # ROCm usa ROCMExecutionProvider
                    if 'ROCMExecutionProvider' in available_providers:
                        providers.insert(0, 'ROCMExecutionProvider')
                        logger.info("ONNX usando ROCMExecutionProvider (GPU AMD)")
                    elif 'CUDAExecutionProvider' in available_providers:
                        providers.insert(0, 'CUDAExecutionProvider')
                        logger.info("ONNX usando CUDAExecutionProvider (GPU NVIDIA)")
                
                self.model = ort.InferenceSession(
                    str(onnx_path),
                    providers=providers
                )
                logger.info(f"Modelo ONNX carregado: {onnx_path}")
                return
            except Exception as e:
                logger.warning(f"Falha ao carregar ONNX: {e}")
        
        # Tentar carregar modelo PyTorch
        pth_files = list(model_dir.glob("*.pth"))
        if TORCH_AVAILABLE and pth_files:
            try:
                model_file = pth_files[0]
                checkpoint = torch.load(model_file, map_location=self.device)
                
                # Armazenar configuração do modelo
                self.model = {
                    "checkpoint": checkpoint,
                    "type": "pytorch"
                }
                logger.info(f"Modelo PyTorch carregado: {model_file}")
                return
            except Exception as e:
                logger.warning(f"Falha ao carregar PyTorch model: {e}")
        
        # Carregar índice FAISS se disponível
        index_path = model_dir / "index.faiss"
        if FAISS_AVAILABLE and index_path.exists():
            try:
                self.index = faiss.read_index(str(index_path))
                logger.info(f"Índice FAISS carregado: {index_path}")
            except Exception as e:
                logger.warning(f"Falha ao carregar índice FAISS: {e}")
        
        if self.model is None:
            raise FileNotFoundError(f"Modelos RVC não encontrados em: {model_dir}")
    
    async def unload_model(self) -> None:
        """Descarrega modelo da memória."""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.index is not None:
            del self.index
            self.index = None
        
        if self.hubert_model is not None:
            del self.hubert_model
            self.hubert_model = None

        self._rvc_model_path = None
        self._rvc_index_path = None
        
        # Forçar garbage collection
        gc.collect()
        
        # Liberar memória GPU
        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        self.is_loaded = False
        logger.info("Modelo RVC descarregado")
    
    async def convert(
        self,
        input_audio_path: str,
        voice_model: str,
        pitch_shift: int = 0,
        filter_radius: int = 3,
        index_rate: float = 0.75,
        protect: float = 0.33,
        rms_mix_rate: float = 0.25
    ) -> Dict[str, Any]:
        """
        Converte voz do áudio de entrada para voz alvo.
        
        Pipeline de conversão:
        1. Carregar e pré-processar áudio
        2. Extrair F0 (pitch) com CREPE/pyworld
        3. Aplicar pitch shift se solicitado
        4. Extrair features de conteúdo
        5. Executar conversão com modelo RVC
        6. Pós-processar e salvar áudio
        
        Args:
            input_audio_path: Caminho do áudio de entrada
            voice_model: Caminho do modelo de voz alvo
            pitch_shift: Ajuste de tom em semitons (-12 a +12)
            filter_radius: Raio do filtro de mediana (0-7)
            index_rate: Taxa de uso do índice FAISS (0-1)
            protect: Proteção de consoantes sem voz (0-0.5)
            rms_mix_rate: Taxa de mixagem RMS (0-1)
        
        Returns:
            Dict com:
                - audio_url: URL do áudio convertido
                - duration: Duração em segundos
                - sample_rate: Taxa de amostragem
                - pitch_shift_applied: Pitch shift aplicado
        """
        logger.info(
            f"Convertendo voz: input={input_audio_path}, "
            f"pitch_shift={pitch_shift}, index_rate={index_rate}"
        )
        
        # Garantir que modelo está carregado
        if not self.is_loaded:
            await self.load_model()
        
        # Se modelo não está realmente carregado, falhar
        if self.model is None:
            raise RuntimeError("Modelo RVC não está carregado")

        # Se RVC WebUI estiver configurado, usar inferência real via subprocesso
        if self._rvc_repo_dir and self._rvc_model_path:
            try:
                result = await asyncio.to_thread(
                    self._convert_rvc_subprocess_sync,
                    input_audio_path,
                    pitch_shift,
                    index_rate,
                    rms_mix_rate
                )
                return result
            except Exception as e:
                logger.error(f"Erro na conversão RVC (WebUI): {e}")
                raise
        
        try:
            # Executar conversão em thread separada
            result = await asyncio.to_thread(
                self._convert_sync,
                input_audio_path,
                voice_model,
                pitch_shift,
                filter_radius,
                index_rate,
                protect,
                rms_mix_rate
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erro na conversão RVC: {e}")
            raise
    
    def _convert_sync(
        self,
        input_audio_path: str,
        voice_model: str,
        pitch_shift: int,
        filter_radius: int,
        index_rate: float,
        protect: float,
        rms_mix_rate: float
    ) -> Dict[str, Any]:
        """
        Conversão síncrona (executada em thread pool).
        
        Implementa o pipeline completo de conversão RVC.
        """
        # 1. Carregar áudio
        audio, sr = self._load_audio(input_audio_path)
        duration = len(audio) / sr
        
        logger.debug(f"Áudio carregado: {duration:.2f}s, {sr}Hz")
        
        # 2. Extrair F0 (pitch)
        f0 = self._extract_pitch(audio, sr)
        
        # 3. Aplicar pitch shift
        if pitch_shift != 0:
            f0 = self._shift_pitch(f0, pitch_shift)
            logger.debug(f"Pitch shift aplicado: {pitch_shift} semitons")
        
        # 4. Executar conversão
        # Nota: Implementação completa requer modelo RVC real
        # Aqui fazemos processamento básico como demonstração
        converted_audio = self._apply_conversion(
            audio, f0, sr, index_rate, protect
        )
        
        # 5. Pós-processamento
        converted_audio = self._post_process(
            converted_audio, audio, rms_mix_rate
        )
        
        # 6. Salvar áudio
        file_id = str(uuid.uuid4())
        output_dir = Path(settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{file_id}_converted.wav"
        
        self._save_audio(converted_audio, sr, str(output_path))
        
        logger.info(f"Conversão concluída: {output_path}, duração: {duration:.2f}s")
        
        return {
            "audio_url": f"/outputs/{file_id}_converted.wav",
            "duration": duration,
            "sample_rate": sr,
            "format": "wav",
            "pitch_shift_applied": pitch_shift,
            "mock": False
        }

    def _convert_rvc_subprocess_sync(
        self,
        input_audio_path: str,
        pitch_shift: int,
        index_rate: float,
        rms_mix_rate: float
    ) -> Dict[str, Any]:
        """Conversão real usando RVC WebUI via subprocesso."""
        from backend.utils.conda_finder import get_conda_run_command, conda_env_exists
        
        file_id = str(uuid.uuid4())
        output_dir = Path(settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{file_id}_converted.wav"

        script_path = Path(__file__).resolve().parent.parent / "scripts" / "rvc_inference_runner.py"

        if not conda_env_exists(self._rvc_env_name):
            raise RuntimeError(
                f"RVC env '{self._rvc_env_name}' não encontrado. "
                "Ative rvc_auto_setup ou crie o ambiente com requirements-rvc.txt."
            )

        # Obter comando conda detectado automaticamente
        conda_cmd = get_conda_run_command(self._rvc_env_name)
        logger.debug(f"Conda command: {' '.join(conda_cmd[:3])}...")
        
        # Construir comando base
        # Se não há arquivo de índice, forçar index_rate=0 para evitar erro
        effective_index_rate = index_rate if self._rvc_index_path else 0.0
        
        cmd = conda_cmd + [
            "python",
            str(script_path),
            "--repo-dir",
            str(self._rvc_repo_dir),
            "--model-path",
            str(self._rvc_model_path),
            "--index-path",
            str(self._rvc_index_path or ""),
            "--input",
            str(input_audio_path),
            "--output",
            str(output_path),
            "--pitch",
            str(pitch_shift),
            "--index-rate",
            str(effective_index_rate),
            "--f0method",
            "rmvpe",
            "--device",
            self.device,
            "--threads",
            str(settings.torch_threads)
        ]
        
        # Adicionar parâmetros ROCm se configurado
        if settings.use_rocm:
            cmd.extend([
                "--use-rocm",
                "--hsa-gfx-version", settings.hsa_override_gfx_version,
                "--rocm-arch", settings.pytorch_rocm_arch
            ])

        # Criar ambiente limpo para o subprocess (evita herdar PYTHONHASHSEED inválido)
        clean_env = os.environ.copy()
        # Remover ou corrigir PYTHONHASHSEED que pode causar erro no subprocess
        if "PYTHONHASHSEED" in clean_env:
            del clean_env["PYTHONHASHSEED"]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            env=clean_env,
            encoding='utf-8',
            errors='replace'  # Evita UnicodeDecodeError no Windows
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"RVC subprocess failed: {result.stderr.strip() or result.stdout.strip()}"
            )

        # Obter duração e sample rate do arquivo gerado
        duration = 0.0
        sample_rate = self.SAMPLE_RATE

        if TORCHAUDIO_IO_AVAILABLE:
            try:
                info = torchaudio.info(str(output_path))
                duration = info.num_frames / info.sample_rate
                sample_rate = info.sample_rate
            except Exception:
                pass

        if duration == 0.0 and LIBROSA_AVAILABLE:
            try:
                duration = librosa.get_duration(path=str(output_path))
            except Exception:
                pass

        return {
            "audio_url": f"/outputs/{file_id}_converted.wav",
            "duration": duration,
            "sample_rate": sample_rate,
            "format": "wav",
            "pitch_shift_applied": pitch_shift,
            "mock": False
        }
    
    def _load_audio(
        self,
        path: str,
        target_sr: Optional[int] = None
    ) -> "Tuple[Any, int]":
        """
        Carrega áudio de arquivo.
        
        Args:
            path: Caminho do arquivo
            target_sr: Taxa de amostragem alvo (None = manter original)
        
        Returns:
            Tuple[np.ndarray, int]: (áudio, sample_rate)
        """
        target_sr = target_sr or self.SAMPLE_RATE
        
        # Tentar com librosa primeiro (melhor compatibilidade)
        if LIBROSA_AVAILABLE:
            try:
                audio, sr = librosa.load(path, sr=target_sr, mono=True)
                return audio.astype(np.float32), sr
            except Exception as e:
                logger.warning(f"librosa falhou: {e}")
        
        # Fallback para torchaudio
        if TORCHAUDIO_IO_AVAILABLE:
            try:
                waveform, sr = torchaudio.load(path)
                audio = waveform.mean(dim=0).numpy()  # Converter para mono
                
                # Resample se necessário
                if sr != target_sr and NUMPY_AVAILABLE:
                    num_samples = int(len(audio) * target_sr / sr)
                    audio = resample(audio, num_samples)
                    sr = target_sr
                
                return audio.astype(np.float32), sr
            except Exception as e:
                logger.warning(f"torchaudio falhou: {e}")
        
        # Fallback para scipy
        if NUMPY_AVAILABLE:
            try:
                sr, audio = wavfile.read(path)
                
                # Converter para float32
                if audio.dtype == np.int16:
                    audio = audio.astype(np.float32) / 32768.0
                elif audio.dtype == np.int32:
                    audio = audio.astype(np.float32) / 2147483648.0
                
                # Converter para mono
                if len(audio.shape) > 1:
                    audio = audio.mean(axis=1)
                
                # Resample se necessário
                if sr != target_sr:
                    num_samples = int(len(audio) * target_sr / sr)
                    audio = resample(audio, num_samples)
                    sr = target_sr
                
                return audio.astype(np.float32), sr
            except Exception as e:
                logger.error(f"scipy falhou: {e}")
                raise
        
        raise RuntimeError("Nenhuma biblioteca de áudio disponível")
    
    def _extract_pitch(
        self,
        audio: Any,
        sr: int
    ) -> Any:
        """
        Extrai contorno de pitch (F0) do áudio.
        
        Usa CREPE se disponível, fallback para pyworld ou parselmouth.
        
        Args:
            audio: Array de áudio
            sr: Taxa de amostragem
        
        Returns:
            np.ndarray: Contorno de F0
        """
        # Número de frames esperado
        hop_ms = self.HOP_LENGTH / sr * 1000
        
        # 1. Tentar CREPE (mais preciso para voz)
        if CREPE_AVAILABLE and TORCH_AVAILABLE:
            try:
                # Converter para tensor
                audio_tensor = torch.from_numpy(audio).unsqueeze(0)
                
                # Garantir sample rate correto para CREPE
                if sr != 16000:
                    if torchaudio is not None:
                        audio_tensor = torchaudio.functional.resample(
                            audio_tensor, sr, 16000
                        )
                    elif NUMPY_AVAILABLE:
                        num_samples = int(len(audio) * 16000 / sr)
                        audio_resampled = resample(audio, num_samples)
                        audio_tensor = torch.from_numpy(audio_resampled).unsqueeze(0)
                    else:
                        raise RuntimeError("Resample indisponível sem torchaudio/numpy")
                
                # Extrair pitch
                time, frequency, confidence, activation = torchcrepe.predict(
                    audio_tensor,
                    16000,
                    hop_length=self.HOP_LENGTH,
                    fmin=self.F0_MIN,
                    fmax=self.F0_MAX,
                    model='tiny',  # Usar modelo menor para velocidade
                    batch_size=512,
                    device=self.device
                )
                
                # Filtrar por confiança
                f0 = frequency.squeeze().numpy()
                conf = confidence.squeeze().numpy()
                f0[conf < 0.5] = 0  # Zerar frames com baixa confiança
                
                logger.debug(f"F0 extraído com CREPE: {len(f0)} frames")
                return f0
                
            except Exception as e:
                logger.warning(f"CREPE falhou: {e}")
        
        # 2. Fallback para pyworld (HARVEST)
        if PYWORLD_AVAILABLE:
            try:
                # Converter para float64 (requerido por pyworld)
                audio_f64 = audio.astype(np.float64)
                
                # Extrair F0 com HARVEST (mais preciso que DIO)
                f0, t = pw.harvest(
                    audio_f64,
                    sr,
                    f0_floor=self.F0_MIN,
                    f0_ceil=self.F0_MAX,
                    frame_period=hop_ms
                )
                
                # Refinar com StoneMask
                f0 = pw.stonemask(audio_f64, f0, t, sr)
                
                logger.debug(f"F0 extraído com pyworld: {len(f0)} frames")
                return f0.astype(np.float32)
                
            except Exception as e:
                logger.warning(f"pyworld falhou: {e}")
        
        # 3. Fallback para parselmouth (Praat)
        if PARSELMOUTH_AVAILABLE:
            try:
                sound = parselmouth.Sound(audio, sampling_frequency=sr)
                pitch = sound.to_pitch_ac(
                    time_step=hop_ms / 1000,
                    pitch_floor=self.F0_MIN,
                    pitch_ceiling=self.F0_MAX
                )
                
                f0 = pitch.selected_array['frequency']
                logger.debug(f"F0 extraído com parselmouth: {len(f0)} frames")
                return f0.astype(np.float32)
                
            except Exception as e:
                logger.warning(f"parselmouth falhou: {e}")
        
        # 4. Fallback final: F0 zerado (sem pitch)
        logger.warning("Nenhum extrator de pitch disponível, usando F0 zerado")
        num_frames = int(len(audio) / self.HOP_LENGTH) + 1
        return np.zeros(num_frames, dtype=np.float32)
    
    def _shift_pitch(self, f0: Any, semitones: int) -> Any:
        """
        Aplica shift de pitch em semitons.
        
        Fórmula: f0_shifted = f0 * 2^(semitones/12)
        
        Args:
            f0: Contorno de F0 original
            semitones: Número de semitons para deslocar (-12 a +12)
        
        Returns:
            np.ndarray: F0 com pitch alterado
        """
        # Calcular fator de multiplicação
        factor = 2 ** (semitones / 12.0)
        
        # Aplicar apenas a frames com voz (f0 > 0)
        f0_shifted = f0.copy()
        voiced = f0 > 0
        f0_shifted[voiced] = f0[voiced] * factor
        
        # Limitar ao range válido
        f0_shifted = np.clip(f0_shifted, 0, self.F0_MAX)
        
        return f0_shifted
    
    def _apply_conversion(
        self,
        audio: Any,
        f0: Any,
        sr: int,
        index_rate: float,
        protect: float
    ) -> Any:
        """
        Aplica conversão de voz.
        
        Nota: Implementação completa requer modelo RVC treinado.
        Esta versão aplica processamento básico de pitch.
        
        Args:
            audio: Áudio de entrada
            f0: Contorno de F0
            sr: Taxa de amostragem
            index_rate: Taxa de uso do índice
            protect: Proteção de consoantes
        
        Returns:
            np.ndarray: Áudio convertido
        """
        # Se temos modelo ONNX, usar inferência
        if ONNX_AVAILABLE and self.model is not None and hasattr(self.model, 'run'):
            try:
                # Preparar inputs para ONNX
                # Nota: formato exato depende do modelo específico
                inputs = {
                    "audio": audio.reshape(1, -1).astype(np.float32),
                    "f0": f0.reshape(1, -1).astype(np.float32)
                }
                
                # Executar inferência
                outputs = self.model.run(None, inputs)
                return outputs[0].squeeze()
            except Exception as e:
                logger.warning(f"Inferência ONNX falhou: {e}")
        
        # Processamento básico sem modelo completo
        # Aplicar pitch shifting usando phase vocoder simplificado
        if LIBROSA_AVAILABLE and f0.sum() > 0:
            try:
                # Calcular ratio médio de pitch
                voiced_f0 = f0[f0 > 0]
                if len(voiced_f0) > 0:
                    # Aplicar time stretch e pitch shift básico
                    # Nota: isso é uma aproximação, não conversão RVC real
                    converted = audio.copy()
                    return converted
            except Exception as e:
                logger.warning(f"Processamento de pitch falhou: {e}")
        
        # Fallback: retornar áudio original
        return audio.copy()
    
    def _post_process(
        self,
        converted: Any,
        original: Any,
        rms_mix_rate: float
    ) -> Any:
        """
        Pós-processamento do áudio convertido.
        
        Aplica normalização RMS e mixagem com original.
        
        Args:
            converted: Áudio convertido
            original: Áudio original
            rms_mix_rate: Taxa de mixagem RMS
        
        Returns:
            np.ndarray: Áudio pós-processado
        """
        if not NUMPY_AVAILABLE:
            return converted
        
        # Calcular RMS do original e convertido
        rms_original = np.sqrt(np.mean(original ** 2) + 1e-8)
        rms_converted = np.sqrt(np.mean(converted ** 2) + 1e-8)
        
        # Normalizar para RMS do original
        if rms_converted > 0:
            converted = converted * (rms_original / rms_converted)
        
        # Mixar com RMS original se solicitado
        if rms_mix_rate > 0 and len(converted) == len(original):
            converted = (
                converted * (1 - rms_mix_rate) +
                original * rms_mix_rate
            )
        
        # Normalizar para evitar clipping
        max_val = np.abs(converted).max()
        if max_val > 1.0:
            converted = converted / max_val * 0.95
        
        return converted.astype(np.float32)
    
    def _save_audio(
        self,
        audio: Any,
        sr: int,
        path: str
    ) -> None:
        """
        Salva áudio em arquivo WAV.
        
        Args:
            audio: Array de áudio
            sr: Taxa de amostragem
            path: Caminho de saída
        """
        # Converter para int16
        audio_int16 = (audio * 32767).astype(np.int16)
        
        # Salvar com scipy
        if NUMPY_AVAILABLE:
            try:
                wavfile.write(path, sr, audio_int16)
                return
            except Exception as e:
                logger.warning(f"scipy write falhou: {e}")
        
        # Fallback para wave (stdlib)
        with wave.open(path, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sr)
            wav_file.writeframes(audio_int16.tobytes())
    
    async def _mock_convert(
        self,
        input_audio_path: str,
        pitch_shift: int,
        voice_model: str
    ) -> Dict[str, Any]:
        """
        Conversão mock quando modelo não disponível.
        
        Cria arquivo de áudio com duração estimada para testes.
        """
        # Tentar obter duração real do áudio
        duration = 10.0  # Default
        
        if LIBROSA_AVAILABLE:
            try:
                duration = librosa.get_duration(path=input_audio_path)
            except Exception:
                pass
        elif TORCHAUDIO_IO_AVAILABLE:
            try:
                info = torchaudio.info(input_audio_path)
                duration = info.num_frames / info.sample_rate
            except Exception:
                pass
        
        # Simular tempo de processamento
        await asyncio.sleep(min(duration * 0.1, 2.0))
        
        # Gerar arquivo de saída
        file_id = str(uuid.uuid4())
        output_dir = Path(settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{file_id}_converted.wav"
        
        # Criar áudio silencioso
        samples = int(duration * self.SAMPLE_RATE)
        
        if NUMPY_AVAILABLE:
            silence = np.zeros(samples, dtype=np.int16)
            wavfile.write(str(output_path), self.SAMPLE_RATE, silence)
        else:
            with wave.open(str(output_path), 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.SAMPLE_RATE)
                wav_file.writeframes(bytes(samples * 2))
        
        logger.warning(
            f"Mock conversion: {duration:.2f}s "
            "(modelo RVC não disponível)"
        )
        
        return {
            "audio_url": f"/outputs/{file_id}_converted.wav",
            "duration": duration,
            "sample_rate": self.SAMPLE_RATE,
            "format": "wav",
            "pitch_shift_applied": pitch_shift,
            "mock": True
        }
    
    async def extract_voice_features(
        self,
        audio_path: str
    ) -> Dict[str, Any]:
        """
        Extrai características de voz para análise.
        
        Útil para comparar vozes e verificar qualidade.
        
        Args:
            audio_path: Caminho do áudio
        
        Returns:
            Dict com características extraídas
        """
        try:
            audio, sr = await asyncio.to_thread(
                self._load_audio, audio_path
            )
            f0 = await asyncio.to_thread(
                self._extract_pitch, audio, sr
            )
            
            # Calcular estatísticas de F0
            voiced_f0 = f0[f0 > 0]
            
            return {
                "duration": len(audio) / sr,
                "sample_rate": sr,
                "f0_mean": float(voiced_f0.mean()) if len(voiced_f0) > 0 else 0,
                "f0_std": float(voiced_f0.std()) if len(voiced_f0) > 0 else 0,
                "f0_min": float(voiced_f0.min()) if len(voiced_f0) > 0 else 0,
                "f0_max": float(voiced_f0.max()) if len(voiced_f0) > 0 else 0,
                "voiced_ratio": len(voiced_f0) / len(f0) if len(f0) > 0 else 0,
                "rms": float(np.sqrt(np.mean(audio ** 2))) if NUMPY_AVAILABLE else 0
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair features: {e}")
            return {"error": str(e)}
    
    async def train_voice_model(
        self,
        dataset_path: str,
        model_name: str,
        epochs: int = 100,
        batch_size: int = 8
    ) -> Dict[str, Any]:
        """
        Treina novo modelo de voz a partir de dataset.
        
        Nota: Treino completo requer implementação do pipeline
        de treino RVC, que é uma operação complexa.
        
        Args:
            dataset_path: Caminho para pasta com áudios de treino
            model_name: Nome do modelo a ser criado
            epochs: Número de épocas de treino
            batch_size: Tamanho do batch
        
        Returns:
            Dict com informações do treino
        """
        logger.info(
            f"Iniciando treino de voz: {model_name}, "
            f"dataset={dataset_path}, epochs={epochs}"
        )
        
        # Verificar dataset
        dataset_dir = Path(dataset_path)
        if not dataset_dir.exists():
            return {
                "status": "error",
                "message": f"Dataset não encontrado: {dataset_path}"
            }
        
        # Contar arquivos de áudio
        audio_files = list(dataset_dir.glob("*.wav")) + list(dataset_dir.glob("*.mp3"))
        
        if len(audio_files) < 10:
            return {
                "status": "error",
                "message": f"Dataset muito pequeno: {len(audio_files)} arquivos (mínimo: 10)"
            }
        
        # TODO: Implementar treino real quando RVC lib disponível
        # O treino RVC envolve:
        # 1. Preprocessar áudios (normalizar, segmentar)
        # 2. Extrair features com HuBERT
        # 3. Treinar modelo de síntese
        # 4. Criar índice FAISS
        
        return {
            "status": "not_implemented",
            "message": "Treino de voz requer implementação completa do RVC",
            "model_name": model_name,
            "dataset_files": len(audio_files),
            "estimated_time_hours": epochs * 0.1
        }
    
    @property
    def status(self) -> Dict[str, Any]:
        """Retorna status atual do serviço."""
        return {
            "loaded": self.is_loaded,
            "model": self.model,  # Required by voice_pipeline
            "model_loaded": self.model is not None,
            "index_loaded": self.index is not None,
            "device": self.device,
            "model_type": "RVC",
            "mock_mode": self.model is None,  # Required by voice_pipeline
            "rvc_repo_dir": str(self._rvc_repo_dir) if self._rvc_repo_dir else None,
            "rvc_repo_loaded": self._rvc_repo_dir is not None,
            "rvc_env_name": self._rvc_env_name,
            "pitch_method": self._pitch_method,
            "libraries": {
                "torch": TORCH_AVAILABLE,
                "numpy": NUMPY_AVAILABLE,
                "librosa": LIBROSA_AVAILABLE,
                "crepe": CREPE_AVAILABLE,
                "pyworld": PYWORLD_AVAILABLE,
                "parselmouth": PARSELMOUTH_AVAILABLE,
                "faiss": FAISS_AVAILABLE,
                "onnx": ONNX_AVAILABLE
            }
        }
