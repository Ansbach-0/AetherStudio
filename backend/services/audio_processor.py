"""
Serviço de processamento de áudio.

Fornece funcionalidades de validação, conversão e normalização
de arquivos de áudio usando pydub e soundfile.
"""

import io
import os
import uuid
from typing import Any, BinaryIO, Dict, List, Optional, Tuple

from backend.config import get_settings
from backend.utils.exceptions import AudioValidationError
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class AudioProcessor:
    """
    Processador de arquivos de áudio.
    
    Responsável por validar, converter e normalizar arquivos
    de áudio antes do processamento pelos modelos ML.
    
    Attributes:
        supported_formats: Formatos de áudio suportados
        max_duration: Duração máxima permitida em segundos
        min_duration: Duração mínima permitida em segundos
        target_sample_rate: Taxa de amostragem alvo
    """
    
    def __init__(self):
        """Inicializa o processador de áudio."""
        self.supported_formats = settings.allowed_audio_formats
        self.max_duration = settings.max_audio_duration
        self.min_duration = settings.min_audio_duration
        self.max_file_size = settings.max_file_size_mb * 1024 * 1024  # bytes
        self.target_sample_rate = 24000
        
        logger.info(
            f"AudioProcessor inicializado: "
            f"formatos={self.supported_formats}, "
            f"duração={self.min_duration}-{self.max_duration}s"
        )
    
    async def validate_and_process(
        self,
        audio_file: BinaryIO,
        filename: str
    ) -> Dict[str, Any]:
        """
        Valida e processa arquivo de áudio.
        
        Realiza validações de formato, tamanho e duração,
        depois converte para formato padronizado.
        
        Args:
            audio_file: Objeto de arquivo de áudio
            filename: Nome original do arquivo
        
        Returns:
            Dict com:
                - path: Caminho do arquivo processado
                - duration: Duração em segundos
                - sample_rate: Taxa de amostragem
                - channels: Número de canais
                - format: Formato do arquivo
        
        Raises:
            AudioValidationError: Se validação falhar
        """
        logger.debug(f"Processando áudio: {filename}")
        
        # Extrair extensão
        ext = self._get_extension(filename)
        if ext not in self.supported_formats:
            raise AudioValidationError(
                f"Formato '{ext}' não suportado. "
                f"Use: {', '.join(self.supported_formats)}"
            )
        
        # Ler conteúdo do arquivo
        content = audio_file.read()
        file_size = len(content)
        
        # Validar tamanho
        if file_size > self.max_file_size:
            raise AudioValidationError(
                f"Arquivo muito grande ({file_size / 1024 / 1024:.1f} MB). "
                f"Máximo: {settings.max_file_size_mb} MB"
            )
        
        # Processar áudio
        try:
            audio_info = await self._process_audio(content, ext)
        except Exception as e:
            logger.error(f"Erro ao processar áudio: {e}")
            raise AudioValidationError(f"Erro ao processar áudio: {str(e)}")
        
        # Validar duração
        duration = audio_info["duration"]
        if duration < self.min_duration:
            raise AudioValidationError(
                f"Áudio muito curto ({duration:.1f}s). "
                f"Mínimo: {self.min_duration}s"
            )
        
        if duration > self.max_duration:
            raise AudioValidationError(
                f"Áudio muito longo ({duration:.1f}s). "
                f"Máximo: {self.max_duration}s"
            )
        
        logger.info(
            f"Áudio validado: {filename}, "
            f"duração={duration:.2f}s, "
            f"sample_rate={audio_info['sample_rate']}"
        )
        
        return audio_info
    
    async def _process_audio(
        self,
        content: bytes,
        format: str
    ) -> Dict[str, Any]:
        """
        Processa conteúdo de áudio.
        
        Converte para WAV normalizado se necessário.
        
        Args:
            content: Bytes do arquivo de áudio
            format: Formato original
        
        Returns:
            Dict com informações do áudio processado
        """
        try:
            from pydub import AudioSegment
        except ImportError:
            logger.warning("pydub não instalado, usando modo fallback")
            # Fallback: salva o arquivo original e estima duração
            file_id = str(uuid.uuid4())
            output_dir = f"{settings.upload_dir}/temp"
            os.makedirs(output_dir, exist_ok=True)
            output_path = f"{output_dir}/{file_id}.wav"
            
            # Cria arquivo físico com conteúdo original
            with open(output_path, "wb") as f:
                f.write(content)
            
            # Estimar duração (muito básico, assume ~16kHz mono 16-bit)
            estimated_duration = len(content) / (16000 * 2)  # bytes / (sample_rate * bytes_per_sample)
            estimated_duration = max(3.0, min(estimated_duration, 60.0))  # Clamp entre 3s e 60s
            
            logger.info(f"Áudio salvo em modo fallback: {output_path}, duração estimada: {estimated_duration:.2f}s")
            
            return {
                "path": output_path,
                "duration": estimated_duration,
                "sample_rate": 24000,  # Assume padrão
                "channels": 1,
                "format": format,
                "fallback_mode": True
            }
        
        # Carregar áudio
        audio_buffer = io.BytesIO(content)
        
        try:
            audio = AudioSegment.from_file(audio_buffer, format=format)
        except Exception as e:
            raise AudioValidationError(f"Não foi possível ler o áudio: {str(e)}")
        
        # Obter informações
        duration = len(audio) / 1000.0  # ms para segundos
        sample_rate = audio.frame_rate
        channels = audio.channels
        
        # Normalizar: mono, sample rate específico
        if channels > 1:
            audio = audio.set_channels(1)
        
        if sample_rate != self.target_sample_rate:
            audio = audio.set_frame_rate(self.target_sample_rate)
        
        # Normalizar volume
        audio = self._normalize_volume(audio)
        
        # Salvar arquivo processado
        file_id = str(uuid.uuid4())
        output_dir = f"{settings.upload_dir}/temp"
        os.makedirs(output_dir, exist_ok=True)
        output_path = f"{output_dir}/{file_id}.wav"
        
        audio.export(output_path, format="wav")
        
        return {
            "path": output_path,
            "duration": duration,
            "sample_rate": self.target_sample_rate,
            "channels": 1,
            "format": "wav"
        }
    
    def _normalize_volume(self, audio: Any) -> Any:
        """
        Normaliza volume do áudio.
        
        Ajusta para -20 dBFS para consistência entre arquivos.
        
        Args:
            audio: AudioSegment do pydub
        
        Returns:
            AudioSegment normalizado
        """
        try:
            from pydub import AudioSegment
            
            target_dBFS = -20.0
            change_in_dBFS = target_dBFS - audio.dBFS
            
            # Limitar alteração para evitar distorção
            if abs(change_in_dBFS) > 20:
                change_in_dBFS = 20 if change_in_dBFS > 0 else -20
            
            return audio.apply_gain(change_in_dBFS)
        except Exception:
            return audio
    
    def _get_extension(self, filename: str) -> str:
        """Extrai extensão do nome do arquivo."""
        if "." not in filename:
            return ""
        return filename.rsplit(".", 1)[-1].lower()
    
    async def convert_format(
        self,
        input_path: str,
        output_format: str = "wav"
    ) -> str:
        """
        Converte arquivo para outro formato.
        
        Args:
            input_path: Caminho do arquivo de entrada
            output_format: Formato de saída desejado
        
        Returns:
            str: Caminho do arquivo convertido
        """
        try:
            from pydub import AudioSegment
        except ImportError:
            raise AudioValidationError("pydub não instalado")
        
        # Detectar formato de entrada
        input_format = self._get_extension(input_path)
        
        if input_format == output_format:
            return input_path
        
        # Carregar e converter
        audio = AudioSegment.from_file(input_path, format=input_format)
        
        # Gerar caminho de saída
        output_path = input_path.rsplit(".", 1)[0] + f".{output_format}"
        
        audio.export(output_path, format=output_format)
        
        logger.info(f"Áudio convertido: {input_format} -> {output_format}")
        
        return output_path
    
    async def trim_audio(
        self,
        input_path: str,
        start_ms: int = 0,
        end_ms: Optional[int] = None
    ) -> str:
        """
        Recorta trecho do áudio.
        
        Args:
            input_path: Caminho do arquivo
            start_ms: Início do corte em milissegundos
            end_ms: Fim do corte (None = até o final)
        
        Returns:
            str: Caminho do arquivo recortado
        """
        try:
            from pydub import AudioSegment
        except ImportError:
            raise AudioValidationError("pydub não instalado")
        
        format = self._get_extension(input_path)
        audio = AudioSegment.from_file(input_path, format=format)
        
        if end_ms is None:
            end_ms = len(audio)
        
        trimmed = audio[start_ms:end_ms]
        
        # Gerar novo nome
        file_id = str(uuid.uuid4())
        output_path = f"{settings.upload_dir}/temp/{file_id}_trimmed.{format}"
        
        trimmed.export(output_path, format=format)
        
        logger.info(f"Áudio recortado: {start_ms}ms - {end_ms}ms")
        
        return output_path
    
    async def get_audio_info(self, file_path: str) -> Dict[str, Any]:
        """
        Obtém informações de um arquivo de áudio.
        
        Args:
            file_path: Caminho do arquivo
        
        Returns:
            Dict com informações do áudio
        """
        try:
            import soundfile as sf
            
            info = sf.info(file_path)
            
            return {
                "duration": info.duration,
                "sample_rate": info.samplerate,
                "channels": info.channels,
                "format": info.format,
                "subtype": info.subtype
            }
        except ImportError:
            logger.warning("soundfile não instalado")
            return {
                "duration": 0,
                "sample_rate": 0,
                "channels": 0,
                "format": "unknown"
            }
        except Exception as e:
            logger.error(f"Erro ao ler info do áudio: {e}")
            raise AudioValidationError(f"Não foi possível ler o arquivo: {str(e)}")
