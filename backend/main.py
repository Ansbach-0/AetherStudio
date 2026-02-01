"""
Entry point da aplicação FastAPI.

Configura a aplicação, middlewares, routers e eventos
de ciclo de vida (startup/shutdown).
"""

from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from backend.config import get_settings

# Configurar logging do SQLAlchemy ANTES de qualquer import
logging.getLogger("sqlalchemy").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.pool").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.orm").setLevel(logging.ERROR)
logging.getLogger("sqlalchemy.dialects").setLevel(logging.ERROR)

# Silenciar logs verbosos de outras bibliotecas
logging.getLogger("opentelemetry").setLevel(logging.ERROR)
logging.getLogger("matplotlib").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.WARNING)
logging.getLogger("faiss").setLevel(logging.WARNING)
logging.getLogger("numba").setLevel(logging.WARNING)
logging.getLogger("librosa").setLevel(logging.WARNING)

from backend.middleware.rate_limiter import limiter
from backend.utils.logger import get_logger, setup_logging

settings = get_settings()

# Configurar HuggingFace cache antes de importar serviços/routers
hf_cache_path = Path(settings.hf_home).resolve()
hf_cache_path.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(hf_cache_path))
os.environ.setdefault("HF_HUB_CACHE", str(hf_cache_path / "hub"))
os.environ.setdefault("TRANSFORMERS_CACHE", str(hf_cache_path / "transformers"))

# Configurar FAISS para usar AVX2 em vez de tentar AVX512
os.environ.setdefault("FAISS_OPT_LEVEL", "avx2")

# Configurar logging no início
setup_logging()
logger = get_logger(__name__)

from backend.routers import health, payment, user, voice, tasks, webhooks


async def check_critical_dependencies():
    """
    Verifica dependências críticas para funcionamento do sistema.
    
    Falha rápido se dependências essenciais estiverem faltando.
    """
    logger.info("Verificando dependências críticas...")
    
    missing_deps = []
    
    # Verificar PyTorch (essencial para TTS e RVC)
    try:
        import torch
        logger.info(f"PyTorch disponível: {torch.__version__}")
    except ImportError:
        missing_deps.append("torch")
    
    # Verificar NumPy (essencial para RVC)
    try:
        import numpy as np
        logger.info(f"NumPy disponível: {np.__version__}")
    except ImportError:
        missing_deps.append("numpy")
    
    # Verificar SciPy (usado para salvar áudio TTS)
    try:
        import scipy
        logger.info(f"SciPy disponível: {scipy.__version__}")
    except ImportError:
        missing_deps.append("scipy")
    
    # Verificar Librosa (usado para carregar áudio RVC)
    try:
        import librosa
        logger.info(f"Librosa disponível: {librosa.__version__}")
    except ImportError:
        missing_deps.append("librosa")
    
    # Verificar F5-TTS (essencial para TTS)
    try:
        from f5_tts.api import F5TTS
        logger.info("F5-TTS disponível")
    except ImportError:
        missing_deps.append("f5-tts")
    
    if missing_deps:
        error_msg = f"Dependências críticas faltando: {', '.join(missing_deps)}. Instale com: pip install {' '.join(missing_deps)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("Todas as dependências críticas verificadas com sucesso!")


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
    
    # Verificar dependências críticas
    await check_critical_dependencies()
    
    # Inicializar detecção do Conda (necessário para RVC subprocess)
    from backend.utils.conda_finder import get_conda_info, ensure_conda_env
    conda_info = get_conda_info()
    if conda_info["conda_found"]:
        logger.info(f"Conda detectado: {conda_info['conda_root']}")
    else:
        logger.warning("Conda não detectado - RVC voice morphing pode não funcionar")

    # Garantir ambiente RVC separado (evita conflito de versões do Hydra)
    if settings.rvc_auto_setup and conda_info["conda_found"]:
        try:
            rvc_result = ensure_conda_env(
                settings.rvc_env_name,
                Path(settings.rvc_requirements_path),
                python_version=settings.rvc_python_version,
            )
            logger.info(
                "RVC env status: %s (created=%s, deps=%s)",
                rvc_result.get("status"),
                rvc_result.get("created"),
                rvc_result.get("dependencies_installed"),
            )
        except Exception as exc:
            logger.error(f"Falha ao preparar ambiente RVC: {exc}")
    
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

# Configurar compressão GZIP (antes do CORS para não interferir)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Configurar CORS
# IMPORTANTE: O CORSMiddleware deve ser o ÚLTIMO middleware adicionado (primeiro a executar)
# para garantir que headers CORS sejam enviados mesmo em respostas de erro (401, 403, etc)
logger.info(f"Configurando CORS para origens: {settings.cors_origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Origens permitidas (ex: http://localhost:5173)
    allow_credentials=True,               # Permitir cookies/tokens de autenticação
    allow_methods=["*"],                  # Permitir todos os métodos HTTP (GET, POST, PUT, DELETE, etc)
    allow_headers=["*"],                  # Permitir todos os headers na requisição
    expose_headers=[                      # Headers que o frontend pode acessar na resposta
        "Content-Length",
        "Content-Type",
        "X-Request-ID",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
    max_age=600,                          # Cache do preflight por 10 minutos (reduz requisições OPTIONS)
)


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
