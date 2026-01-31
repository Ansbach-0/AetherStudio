"""
Middleware de Rate Limiting.

Limita quantidade de requisições por IP/usuário
para proteger a API contra abusos.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.config import get_settings

settings = get_settings()


def get_identifier(request) -> str:
    """
    Obtém identificador único para rate limiting.
    
    Usa IP do cliente. Em produção, considere usar
    também API key ou user_id para limites por usuário.
    
    Args:
        request: Objeto de requisição FastAPI
    
    Returns:
        str: Identificador único (IP ou user_id)
    """
    # Tentar obter user_id do query param ou header
    user_id = request.query_params.get("user_id")
    if user_id:
        return f"user:{user_id}"
    
    # Fallback para IP
    return get_remote_address(request)


# Criar instância do limiter
# Usa memória como storage por padrão (em produção, use Redis)
limiter = Limiter(
    key_func=get_identifier,
    default_limits=[f"{settings.rate_limit_requests}/minute"]
)


# Decoradores de rate limit para uso nos endpoints
# Exemplo de uso:
#
# @router.get("/expensive-operation")
# @limiter.limit("5/minute")
# async def expensive_operation(request: Request):
#     ...

# Limites personalizados por tipo de operação
RATE_LIMITS = {
    # Operações de leitura (mais permissivas)
    "read": f"{settings.rate_limit_requests * 2}/minute",
    
    # Operações de escrita
    "write": f"{settings.rate_limit_requests}/minute",
    
    # Operações pesadas (ML inference)
    "heavy": "10/minute",
    
    # Criação de conta
    "register": "5/hour",
    
    # Downloads
    "download": "30/minute",
}


def get_limit_for_operation(operation: str) -> str:
    """
    Retorna limite configurado para um tipo de operação.
    
    Args:
        operation: Tipo de operação (read, write, heavy, etc.)
    
    Returns:
        str: String de limite no formato "N/period"
    """
    return RATE_LIMITS.get(operation, RATE_LIMITS["write"])
