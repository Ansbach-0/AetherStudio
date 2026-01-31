"""
Exceções customizadas da aplicação.

Define hierarquia de exceções para tratamento de erros
específicos do domínio de voice cloning.
"""

from typing import Any, Optional

from fastapi import HTTPException, status


class VoiceCloneException(Exception):
    """
    Exceção base para erros de voice cloning.
    
    Todas as exceções de domínio devem herdar desta classe.
    
    Attributes:
        message: Mensagem de erro
        code: Código de erro para identificação
        details: Detalhes adicionais do erro
    """
    
    def __init__(
        self,
        message: str,
        code: str = "VOICE_CLONE_ERROR",
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> dict[str, Any]:
        """Converte exceção para dicionário."""
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details
        }


class AudioValidationError(VoiceCloneException, HTTPException):
    """
    Erro de validação de áudio.
    
    Levantado quando um arquivo de áudio não passa
    nas validações de formato, duração ou qualidade.
    
    Example:
        raise AudioValidationError("Formato WAV obrigatório")
    """
    
    def __init__(self, message: str, details: Optional[dict] = None):
        VoiceCloneException.__init__(
            self,
            message=message,
            code="AUDIO_VALIDATION_ERROR",
            details=details
        )
        HTTPException.__init__(
            self,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )


class InsufficientCreditsError(VoiceCloneException, HTTPException):
    """
    Erro de créditos insuficientes.
    
    Levantado quando usuário tenta realizar operação
    sem créditos suficientes.
    
    Attributes:
        available: Créditos disponíveis
        required: Créditos necessários
    """
    
    def __init__(self, available: float, required: float):
        message = (
            f"Créditos insuficientes. "
            f"Disponível: {available:.2f}, Necessário: {required:.2f}"
        )
        VoiceCloneException.__init__(
            self,
            message=message,
            code="INSUFFICIENT_CREDITS",
            details={"available": available, "required": required}
        )
        HTTPException.__init__(
            self,
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=message
        )
        self.available = available
        self.required = required


class UserNotFoundError(VoiceCloneException, HTTPException):
    """
    Erro de usuário não encontrado.
    
    Levantado quando operação referencia usuário inexistente.
    """
    
    def __init__(self, user_id: int):
        message = f"Usuário não encontrado: {user_id}"
        VoiceCloneException.__init__(
            self,
            message=message,
            code="USER_NOT_FOUND",
            details={"user_id": user_id}
        )
        HTTPException.__init__(
            self,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


class UserAlreadyExistsError(VoiceCloneException, HTTPException):
    """
    Erro de usuário já existente.
    
    Levantado na tentativa de criar usuário com email duplicado.
    """
    
    def __init__(self, email: str):
        message = f"Usuário já cadastrado com este email: {email}"
        VoiceCloneException.__init__(
            self,
            message=message,
            code="USER_ALREADY_EXISTS",
            details={"email": email}
        )
        HTTPException.__init__(
            self,
            status_code=status.HTTP_409_CONFLICT,
            detail=message
        )


class VoiceProfileNotFoundError(VoiceCloneException, HTTPException):
    """
    Erro de perfil de voz não encontrado.
    
    Levantado quando operação referencia perfil inexistente
    ou sem permissão de acesso.
    """
    
    def __init__(self, profile_id: int):
        message = f"Perfil de voz não encontrado: {profile_id}"
        VoiceCloneException.__init__(
            self,
            message=message,
            code="VOICE_PROFILE_NOT_FOUND",
            details={"profile_id": profile_id}
        )
        HTTPException.__init__(
            self,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


class ModelNotLoadedError(VoiceCloneException, HTTPException):
    """
    Erro de modelo ML não carregado.
    
    Levantado quando operação requer modelo que não está em memória.
    """
    
    def __init__(self, model_name: str):
        message = f"Modelo não carregado: {model_name}"
        VoiceCloneException.__init__(
            self,
            message=message,
            code="MODEL_NOT_LOADED",
            details={"model": model_name}
        )
        HTTPException.__init__(
            self,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=message
        )


class RateLimitExceededError(VoiceCloneException, HTTPException):
    """
    Erro de rate limit excedido.
    
    Levantado quando usuário excede limite de requisições.
    """
    
    def __init__(self, limit: int, period: int):
        message = f"Limite de requisições excedido: {limit} por {period}s"
        VoiceCloneException.__init__(
            self,
            message=message,
            code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "period_seconds": period}
        )
        HTTPException.__init__(
            self,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message
        )


class ProcessingError(VoiceCloneException, HTTPException):
    """
    Erro genérico de processamento.
    
    Levantado quando ocorre erro durante processamento de áudio ou ML.
    """
    
    def __init__(self, message: str, details: Optional[dict] = None):
        VoiceCloneException.__init__(
            self,
            message=message,
            code="PROCESSING_ERROR",
            details=details
        )
        HTTPException.__init__(
            self,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=message
        )
