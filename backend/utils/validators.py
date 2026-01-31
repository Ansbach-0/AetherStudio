"""
Validadores de entrada.

Funções de validação reutilizáveis para dados de entrada da API.
"""

import re
from typing import List, Optional

from backend.config import get_settings
from backend.utils.exceptions import AudioValidationError

settings = get_settings()


def validate_email(email: str) -> bool:
    """
    Valida formato de email.
    
    Args:
        email: Endereço de email a validar
    
    Returns:
        bool: True se email é válido
    
    Example:
        if not validate_email(user_input):
            raise ValueError("Email inválido")
    """
    # Regex básico para validação de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_language(language: str) -> bool:
    """
    Valida código de idioma.
    
    Args:
        language: Código do idioma (ex: "pt-BR")
    
    Returns:
        bool: True se idioma é suportado
    """
    return language in settings.allowed_languages


def validate_audio_format(filename: str) -> bool:
    """
    Valida formato de arquivo de áudio pela extensão.
    
    Args:
        filename: Nome do arquivo
    
    Returns:
        bool: True se formato é suportado
    """
    if "." not in filename:
        return False
    
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in settings.allowed_audio_formats


def validate_text_length(
    text: str,
    min_length: int = 1,
    max_length: int = 5000
) -> bool:
    """
    Valida comprimento de texto.
    
    Args:
        text: Texto a validar
        min_length: Comprimento mínimo
        max_length: Comprimento máximo
    
    Returns:
        bool: True se texto está dentro dos limites
    """
    length = len(text.strip())
    return min_length <= length <= max_length


def validate_speed(speed: float) -> bool:
    """
    Valida velocidade de síntese.
    
    Args:
        speed: Velocidade (0.5 a 2.0)
    
    Returns:
        bool: True se velocidade é válida
    """
    return 0.5 <= speed <= 2.0


def validate_pitch_shift(pitch: int) -> bool:
    """
    Valida ajuste de tom.
    
    Args:
        pitch: Ajuste em semitons (-12 a +12)
    
    Returns:
        bool: True se ajuste é válido
    """
    return -12 <= pitch <= 12


def sanitize_filename(filename: str) -> str:
    """
    Sanitiza nome de arquivo removendo caracteres perigosos.
    
    Args:
        filename: Nome original do arquivo
    
    Returns:
        str: Nome sanitizado
    
    Example:
        safe_name = sanitize_filename("../../../etc/passwd")
        # Retorna: "etcpasswd"
    """
    # Remover caracteres perigosos
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    safe_name = filename
    
    for char in dangerous_chars:
        safe_name = safe_name.replace(char, '')
    
    # Remover espaços no início e fim
    safe_name = safe_name.strip()
    
    # Se ficou vazio, usar nome genérico
    if not safe_name:
        safe_name = "unnamed_file"
    
    return safe_name


def validate_user_id(user_id: int) -> bool:
    """
    Valida ID de usuário.
    
    Args:
        user_id: ID do usuário
    
    Returns:
        bool: True se ID é válido
    """
    return isinstance(user_id, int) and user_id > 0


def validate_profile_name(name: str) -> tuple[bool, Optional[str]]:
    """
    Valida nome de perfil de voz.
    
    Args:
        name: Nome do perfil
    
    Returns:
        tuple: (é_válido, mensagem_erro)
    """
    if not name or not name.strip():
        return False, "Nome não pode ser vazio"
    
    if len(name) > 100:
        return False, "Nome muito longo (máximo 100 caracteres)"
    
    # Verificar caracteres válidos
    if not re.match(r'^[\w\s\-\.]+$', name, re.UNICODE):
        return False, "Nome contém caracteres inválidos"
    
    return True, None


class AudioValidator:
    """
    Classe para validação completa de arquivos de áudio.
    
    Agrupa validações relacionadas a arquivos de áudio
    com configurações customizáveis.
    """
    
    def __init__(
        self,
        allowed_formats: Optional[List[str]] = None,
        max_size_mb: Optional[int] = None,
        max_duration: Optional[int] = None,
        min_duration: Optional[int] = None
    ):
        """
        Inicializa validador com configurações.
        
        Args:
            allowed_formats: Formatos permitidos (usa config se None)
            max_size_mb: Tamanho máximo em MB
            max_duration: Duração máxima em segundos
            min_duration: Duração mínima em segundos
        """
        self.allowed_formats = allowed_formats or settings.allowed_audio_formats
        self.max_size_mb = max_size_mb or settings.max_file_size_mb
        self.max_duration = max_duration or settings.max_audio_duration
        self.min_duration = min_duration or settings.min_audio_duration
    
    def validate_format(self, filename: str) -> None:
        """
        Valida formato do arquivo.
        
        Raises:
            AudioValidationError: Se formato não suportado
        """
        if not validate_audio_format(filename):
            ext = filename.rsplit(".", 1)[-1] if "." in filename else "none"
            raise AudioValidationError(
                f"Formato '{ext}' não suportado. "
                f"Use: {', '.join(self.allowed_formats)}"
            )
    
    def validate_size(self, size_bytes: int) -> None:
        """
        Valida tamanho do arquivo.
        
        Raises:
            AudioValidationError: Se arquivo muito grande
        """
        max_bytes = self.max_size_mb * 1024 * 1024
        if size_bytes > max_bytes:
            raise AudioValidationError(
                f"Arquivo muito grande ({size_bytes / 1024 / 1024:.1f} MB). "
                f"Máximo: {self.max_size_mb} MB"
            )
    
    def validate_duration(self, duration_seconds: float) -> None:
        """
        Valida duração do áudio.
        
        Raises:
            AudioValidationError: Se duração fora dos limites
        """
        if duration_seconds < self.min_duration:
            raise AudioValidationError(
                f"Áudio muito curto ({duration_seconds:.1f}s). "
                f"Mínimo: {self.min_duration}s"
            )
        
        if duration_seconds > self.max_duration:
            raise AudioValidationError(
                f"Áudio muito longo ({duration_seconds:.1f}s). "
                f"Máximo: {self.max_duration}s"
            )
