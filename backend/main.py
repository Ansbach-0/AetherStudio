"""
Entry point da aplicação FastAPI.

Configura a aplicação, middlewares, routers e eventos
de ciclo de vida (startup/shutdown).
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.config import get_settings
from backend.middleware.rate_limiter import limiter
from backend.routers import health, payment, user, voice, tasks, webhooks
from backend.utils.logger import get_logger, setup_logging

# Configurar logging no início
setup_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gerencia o ciclo de vida da aplicação.
    
    Startup:
        - Cria diretórios necessários
        - Inicializa conexão com banco de dados
        - Carrega modelos ML em memória (placeholder)
    
    Shutdown:
        - Libera recursos de GPU
        - Fecha conexões com banco
        - Limpa arquivos temporários
    """
    # === STARTUP ===
    logger.info("Iniciando aplicação Voice Cloning SaaS...")
    
    # Criar diretórios necessários
    import os
    for directory in [settings.upload_dir, settings.models_dir, settings.output_dir]:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Diretório verificado: {directory}")
    
    # Inicializar banco de dados
    from backend.models.database import init_db
    await init_db()
    logger.info("Banco de dados inicializado")
    
    # Placeholder: Carregar modelos ML
    # TODO: Implementar carregamento real dos modelos F5-TTS e RVC
    logger.info("Modelos ML: usando placeholders (desenvolvimento)")
    
    # Verificar disponibilidade de GPU
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"GPU disponível: {gpu_name}")
        else:
            logger.warning("GPU não disponível, usando CPU")
    except ImportError:
        logger.warning("PyTorch não instalado, funcionalidades ML limitadas")
    
    # Montar diretórios estáticos (após garantir que existem)
    app.mount("/outputs", StaticFiles(directory=settings.output_dir), name="outputs")
    app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
    logger.info("Diretórios estáticos montados: /outputs, /uploads")
    
    logger.info("Aplicação iniciada com sucesso!")
    
    yield  # Aplicação rodando
    
    # === SHUTDOWN ===
    logger.info("Encerrando aplicação...")
    
    # Liberar recursos de GPU
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("Cache da GPU limpo")
    except ImportError:
        pass
    
    logger.info("Aplicação encerrada com sucesso!")


# Criar aplicação FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## Voice Cloning SaaS API
    
    API para clonagem e conversão de voz utilizando modelos de IA.
    
    ### Funcionalidades:
    - **Clonagem de Voz**: Clone vozes a partir de amostras de áudio
    - **Conversão de Voz**: Converta sua voz para outras vozes
    - **Perfis de Voz**: Gerencie perfis de voz salvos
    - **Sistema de Créditos**: Controle de uso e cobrança
    
    ### Idiomas Suportados:
    - Português (Brasil)
    - Inglês (EUA)
    - Espanhol (Espanha)
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Configurar rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar compressão GZIP
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Middleware de logging de requisições HTTP
@app.middleware("http")
async def log_requests(request, call_next):
    """
    Middleware para logging de todas as requisições HTTP.
    Adiciona request_id único e loga tempo de resposta.
    """
    import time
    import uuid
    from backend.utils.logger import request_id_ctx
    
    # Gera request_id único
    req_id = str(uuid.uuid4())[:8]
    request_id_ctx.set(req_id)
    
    start_time = time.time()
    method = request.method
    path = request.url.path
    
    # Log de entrada (apenas para endpoints não triviais)
    if not path.startswith("/health") and path != "/":
        logger.info(
            "Requisição iniciada",
            method=method,
            path=path,
            client_ip=request.client.host if request.client else None,
        )
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # Log de resposta (apenas para endpoints não triviais)
        if not path.startswith("/health") and path != "/":
            log_method = logger.info if response.status_code < 400 else logger.warning
            log_method(
                "Requisição concluída",
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(duration * 1000, 2),
            )
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "Requisição falhou",
            method=method,
            path=path,
            duration_ms=round(duration * 1000, 2),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise


# Incluir routers
app.include_router(health.router)
app.include_router(user.router, prefix="/api/v1")
app.include_router(voice.router, prefix="/api/v1")
app.include_router(payment.router, prefix="/api/v1")
app.include_router(tasks.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")

# Diretórios estáticos são montados no lifespan após criação


@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raiz da API.
    
    Retorna informações básicas sobre a API e links úteis.
    """
    return {
        "message": f"Bem-vindo à {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
