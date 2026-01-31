"""
Endpoints para gerenciamento de tarefas em background.

Permite consultar status, listar e cancelar tarefas assíncronas.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from backend.services.background_tasks import get_task_manager, TaskStatus
from backend.utils.logger import get_logger

router = APIRouter(prefix="/tasks", tags=["Tasks"])
logger = get_logger(__name__)


@router.get(
    "/{task_id}",
    summary="Consultar status de tarefa",
    description="Retorna status e resultado de uma tarefa em background."
)
async def get_task_status(task_id: str):
    """
    Consulta status de uma tarefa.
    
    Args:
        task_id: ID único da tarefa
    
    Returns:
        Informações da tarefa incluindo status, progresso e resultado
    
    Raises:
        HTTPException 404: Tarefa não encontrada
    """
    task_manager = get_task_manager()
    task_status = await task_manager.get_status(task_id)
    
    if not task_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task_status


@router.get(
    "",
    summary="Listar tarefas",
    description="Lista tarefas em background com filtros opcionais."
)
async def list_tasks(
    status_filter: Optional[str] = Query(
        None,
        description="Filtrar por status (pending, processing, completed, failed)"
    ),
    limit: int = Query(50, ge=1, le=200, description="Número máximo de resultados")
):
    """
    Lista tarefas registradas no sistema.
    
    Args:
        status_filter: Filtro opcional por status
        limit: Limite de resultados
    
    Returns:
        Lista de tarefas com informações básicas
    """
    task_manager = get_task_manager()
    
    # Validar e converter filtro de status
    parsed_status = None
    if status_filter:
        try:
            parsed_status = TaskStatus(status_filter)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {[s.value for s in TaskStatus]}"
            )
    
    tasks = await task_manager.list_tasks(status_filter=parsed_status, limit=limit)
    
    return {
        "tasks": tasks,
        "count": len(tasks)
    }


@router.post(
    "/{task_id}/cancel",
    summary="Cancelar tarefa",
    description="Cancela uma tarefa pendente."
)
async def cancel_task(task_id: str):
    """
    Tenta cancelar uma tarefa pendente.
    
    Apenas tarefas com status 'pending' podem ser canceladas.
    Tarefas já em execução não podem ser interrompidas.
    
    Args:
        task_id: ID da tarefa
    
    Returns:
        Confirmação de cancelamento
    
    Raises:
        HTTPException 400: Tarefa não pode ser cancelada
        HTTPException 404: Tarefa não encontrada
    """
    task_manager = get_task_manager()
    
    # Verificar se tarefa existe
    task_status = await task_manager.get_status(task_id)
    if not task_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Tentar cancelar
    cancelled = await task_manager.cancel_task(task_id)
    
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot be cancelled (already processing or completed)"
        )
    
    logger.info(f"Task {task_id[:8]} cancelada pelo usuário")
    
    return {
        "task_id": task_id,
        "status": "cancelled",
        "message": "Task cancelled successfully"
    }


@router.get(
    "/stats/summary",
    summary="Estatísticas de tarefas",
    description="Retorna estatísticas do sistema de tarefas."
)
async def get_task_stats():
    """
    Retorna estatísticas do gerenciador de tarefas.
    
    Returns:
        Contagens por status e informações gerais
    """
    task_manager = get_task_manager()
    return task_manager.stats


@router.post(
    "/cleanup",
    summary="Limpar tarefas antigas",
    description="Remove tarefas completadas há mais de X horas."
)
async def cleanup_tasks(
    max_age_hours: int = Query(24, ge=1, le=168, description="Idade máxima em horas")
):
    """
    Remove tarefas antigas do sistema.
    
    Args:
        max_age_hours: Tarefas completadas há mais de X horas serão removidas
    
    Returns:
        Número de tarefas removidas
    """
    task_manager = get_task_manager()
    removed = await task_manager.cleanup_old_tasks(max_age_hours)
    
    return {
        "removed_count": removed,
        "max_age_hours": max_age_hours
    }
