"""
Configuração de logging estruturado.

Utiliza structlog para logs em formato JSON em produção
e formato colorido para desenvolvimento.

Inclui middleware para logging de requisições HTTP com
contexto automaticamente adicionado.
"""

import logging
import sys
import time
import uuid
from typing import Any, Callable
from contextvars import ContextVar

import structlog
from structlog.types import Processor

from backend.config import get_settings

# Context var para armazenar request_id por requisição
request_id_ctx: ContextVar[str] = ContextVar('request_id', default='')


def setup_logging() -> None:
    """
    Configura o sistema de logging da aplicação.
    
    Em modo debug: logs coloridos e formatados para terminal.
    Em produção: logs em JSON para processamento por ferramentas.
    """
    settings = get_settings()
    
    # Definir nível de log
    log_level = logging.DEBUG if settings.debug else logging.INFO
    
    # Processadores comuns
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        add_request_id,  # Adiciona request_id automaticamente
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    
    if settings.debug:
        # Desenvolvimento: logs coloridos no terminal
        processors: list[Processor] = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # Produção: logs em JSON
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ]
    
    # Configurar structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configurar logging padrão do Python para bibliotecas externas
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )
    
    # Silenciar logs verbosos de bibliotecas
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )


def add_request_id(logger: Any, method_name: str, event_dict: dict) -> dict:
    """
    Processador que adiciona request_id ao evento de log se disponível.
    """
    req_id = request_id_ctx.get()
    if req_id:
        event_dict['request_id'] = req_id
    return event_dict


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Obtém logger configurado para um módulo.
    
    Args:
        name: Nome do módulo (geralmente __name__)
    
    Returns:
        structlog.BoundLogger: Logger configurado
    
    Example:
        logger = get_logger(__name__)
        logger.info("Operação concluída", user_id=123, duration=1.5)
    """
    return structlog.get_logger(name)


class RequestLoggingMiddleware:
    """
    Middleware ASGI para logging automático de requisições HTTP.
    
    Adiciona request_id único, loga entrada/saída e tempo de resposta.
    """
    
    def __init__(self, app):
        self.app = app
        self.logger = get_logger("http")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        # Gera request_id único
        req_id = str(uuid.uuid4())[:8]
        request_id_ctx.set(req_id)
        
        # Extrai informações da requisição
        method = scope.get("method", "?")
        path = scope.get("path", "?")
        query = scope.get("query_string", b"").decode()
        client = scope.get("client", ("?", 0))
        
        # Log de entrada
        start_time = time.time()
        self.logger.info(
            "Requisição iniciada",
            method=method,
            path=path,
            query=query[:100] if query else None,
            client_ip=client[0] if client else None,
        )
        
        # Intercepta response para capturar status_code
        status_code = 0
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            return await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            # Log de erro
            duration = time.time() - start_time
            self.logger.error(
                "Requisição falhou",
                method=method,
                path=path,
                duration_ms=round(duration * 1000, 2),
                error=str(e),
                error_type=type(e).__name__,
            )
            raise
        else:
            # Log de sucesso
            duration = time.time() - start_time
            log_method = self.logger.info if status_code < 400 else self.logger.warning
            log_method(
                "Requisição concluída",
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=round(duration * 1000, 2),
            )


class LoggerAdapter:
    """
    Adaptador para uso do logger em contextos específicos.
    
    Permite adicionar contexto permanente ao logger,
    útil para requisições ou operações longas.
    
    Example:
        logger = LoggerAdapter(get_logger(__name__))
        logger.bind(request_id="abc-123", user_id=1)
        logger.info("Processando")  # Inclui request_id e user_id
    """
    
    def __init__(self, logger: structlog.BoundLogger):
        self._logger = logger
        self._context: dict[str, Any] = {}
    
    def bind(self, **kwargs: Any) -> "LoggerAdapter":
        """Adiciona contexto ao logger."""
        self._context.update(kwargs)
        self._logger = self._logger.bind(**kwargs)
        return self
    
    def unbind(self, *keys: str) -> "LoggerAdapter":
        """Remove contexto do logger."""
        for key in keys:
            self._context.pop(key, None)
        self._logger = self._logger.unbind(*keys)
        return self
    
    def debug(self, msg: str, **kwargs: Any) -> None:
        self._logger.debug(msg, **kwargs)
    
    def info(self, msg: str, **kwargs: Any) -> None:
        self._logger.info(msg, **kwargs)
    
    def warning(self, msg: str, **kwargs: Any) -> None:
        self._logger.warning(msg, **kwargs)
    
    def error(self, msg: str, **kwargs: Any) -> None:
        self._logger.error(msg, **kwargs)
    
    def exception(self, msg: str, **kwargs: Any) -> None:
        self._logger.exception(msg, **kwargs)
