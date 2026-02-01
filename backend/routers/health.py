"""
Endpoints de health check e monitoramento.

Fornece endpoints para verificar status da API e recursos do sistema.
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from backend.config import get_settings
from backend.models.schemas import GPUStatusResponse, HealthResponse
from backend.services.cache_service import get_cache_service
from backend.services.background_tasks import get_task_manager

router = APIRouter(prefix="/health", tags=["Health"])
settings = get_settings()


async def check_dependencies():
    """
    Verifica status das dependências críticas.
    
    Returns:
        dict: Status de cada dependência
    """
    deps = {}
    
    # PyTorch
    try:
        import torch
        deps["torch"] = {"available": True, "version": torch.__version__}
    except ImportError:
        deps["torch"] = {"available": False, "version": None}
    
    # NumPy
    try:
        import numpy as np
        deps["numpy"] = {"available": True, "version": np.__version__}
    except ImportError:
        deps["numpy"] = {"available": False, "version": None}
    
    # SciPy
    try:
        import scipy
        deps["scipy"] = {"available": True, "version": scipy.__version__}
    except ImportError:
        deps["scipy"] = {"available": False, "version": None}
    
    # Librosa
    try:
        import librosa
        deps["librosa"] = {"available": True, "version": librosa.__version__}
    except ImportError:
        deps["librosa"] = {"available": False, "version": None}
    
    # F5-TTS
    try:
        from f5_tts.api import F5TTS
        deps["f5_tts"] = {"available": True, "version": "installed"}
    except ImportError:
        deps["f5_tts"] = {"available": False, "version": None}
    
    # Verificar se todas críticas estão disponíveis
    critical_deps = ["torch", "numpy", "scipy", "librosa", "f5_tts"]
    all_available = all(deps[dep]["available"] for dep in critical_deps)
    
    return {
        "all_available": all_available,
        "dependencies": deps
    }


@router.get(
    "",
    response_model=HealthResponse,
    summary="Status da API",
    description="Verifica se a API está funcionando corretamente."
)
async def health_check() -> HealthResponse:
    """
    Endpoint de health check básico.
    
    Retorna status da API, versão e timestamp atual.
    Útil para load balancers e monitoramento.
    
    Returns:
        HealthResponse: Status da API
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc)
    )


@router.get(
    "/gpu",
    response_model=GPUStatusResponse,
    summary="Status da GPU",
    description="Verifica disponibilidade e uso da GPU para inferência ML."
)
async def gpu_status() -> GPUStatusResponse:
    """
    Verifica status da GPU via PyTorch.
    
    Retorna informações sobre disponibilidade, memória e versão CUDA.
    
    Returns:
        GPUStatusResponse: Informações da GPU
    """
    try:
        import torch
        
        if torch.cuda.is_available():
            # Obter informações da GPU
            device_name = torch.cuda.get_device_name(0)
            memory_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            memory_reserved = torch.cuda.memory_reserved(0) / (1024**3)
            cuda_version = torch.version.cuda
            
            return GPUStatusResponse(
                available=True,
                device_name=device_name,
                memory_total_gb=round(memory_total, 2),
                memory_used_gb=round(memory_reserved, 2),
                cuda_version=cuda_version
            )
        else:
            return GPUStatusResponse(
                available=False,
                device_name="CPU Only",
                memory_total_gb=None,
                memory_used_gb=None,
                cuda_version=None
            )
    except ImportError:
        return GPUStatusResponse(
            available=False,
            device_name="PyTorch not installed",
            memory_total_gb=None,
            memory_used_gb=None,
            cuda_version=None
        )
    except Exception as e:
        return GPUStatusResponse(
            available=False,
            device_name=f"Error: {str(e)}",
            memory_total_gb=None,
            memory_used_gb=None,
            cuda_version=None
        )


@router.get(
    "/detailed",
    summary="Detailed Health Check",
    description="Retorna status detalhado da API incluindo GPU."
)
async def detailed_health():
    """
    Health check detalhado com informações de GPU.
    
    Returns:
        dict: Status completo da API
    """
    gpu_info = await gpu_status()
    cache_service = get_cache_service()
    task_manager = get_task_manager()
    
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gpu": {
            "available": gpu_info.available,
            "name": gpu_info.device_name,
            "memory_total_gb": gpu_info.memory_total_gb,
            "memory_used_gb": gpu_info.memory_used_gb,
        },
        "cache": cache_service.status,
        "tasks": task_manager.stats
    }


@router.get(
    "/ready",
    summary="Readiness Check",
    description="Verifica se a API está pronta para receber requisições."
)
async def readiness_check():
    """
    Verifica se todos os serviços necessários estão prontos.
    
    Diferente do health check, verifica dependências como
    banco de dados e modelos ML.
    
    Returns:
        dict: Status de prontidão com detalhes
    """
    # Verificar dependências críticas
    deps_status = await check_dependencies()
    
    # Obter status dos serviços
    cache_service = get_cache_service()
    task_manager = get_task_manager()
    
    checks = {
        "database": True,    # Placeholder: verificar conexão real
        "models_loaded": True,  # Placeholder: verificar modelos
        "disk_space": True,   # Placeholder: verificar espaço
        "cache": cache_service.status["memory_cache"]["size"] >= 0,
        "task_manager": True,
        "dependencies": deps_status["all_available"]
    }
    
    all_ready = all(checks.values())
    
    return {
        "ready": all_ready,
        "checks": checks,
        "dependencies": deps_status,
        "cache_stats": cache_service.status,
        "task_stats": task_manager.stats,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
