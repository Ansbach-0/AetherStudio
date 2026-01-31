"""
Gerenciador de tarefas assíncronas em background.

Permite processar operações longas (TTS, RVC) em background
retornando um task_id para consulta posterior.
"""

import asyncio
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass, field

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class TaskStatus(str, Enum):
    """Status possíveis de uma tarefa."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackgroundTask:
    """Representa uma tarefa em background."""
    id: str
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BackgroundTaskManager:
    """
    Gerencia execução de tarefas em background.
    
    Features:
    - Limite de tarefas concorrentes
    - Tracking de progresso
    - Limpeza automática de tarefas antigas
    """
    
    def __init__(self, max_concurrent: Optional[int] = None):
        self._tasks: Dict[str, BackgroundTask] = {}
        self._semaphore = asyncio.Semaphore(
            max_concurrent or settings.max_concurrent_tasks
        )
        self._lock = asyncio.Lock()
    
    async def submit(
        self,
        func: Callable,
        *args,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Submete função para execução em background.
        
        Args:
            func: Função a ser executada
            *args: Argumentos posicionais
            metadata: Metadados adicionais da tarefa
            **kwargs: Argumentos nomeados
        
        Returns:
            str: ID único da tarefa
        """
        task_id = str(uuid.uuid4())
        
        task = BackgroundTask(
            id=task_id,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )
        
        async with self._lock:
            self._tasks[task_id] = task
        
        # Agendar execução
        asyncio.create_task(self._execute(task_id, func, *args, **kwargs))
        
        logger.info(f"Task {task_id[:8]} submetida para execução em background")
        return task_id
    
    async def _execute(self, task_id: str, func: Callable, *args, **kwargs):
        """Executa tarefa com controle de concorrência."""
        async with self._semaphore:
            task = self._tasks[task_id]
            task.status = TaskStatus.PROCESSING
            
            logger.debug(f"Task {task_id[:8]} iniciada")
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = await asyncio.to_thread(func, *args, **kwargs)
                
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = datetime.utcnow()
                task.progress = 100.0
                
                logger.info(f"Task {task_id[:8]} completada com sucesso")
                
            except Exception as e:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.utcnow()
                logger.error(f"Task {task_id[:8]} falhou: {e}")
    
    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retorna status de uma tarefa.
        
        Args:
            task_id: ID da tarefa
        
        Returns:
            Dict com informações da tarefa ou None se não encontrada
        """
        task = self._tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.id,
            "status": task.status.value,
            "progress": task.progress,
            "created_at": task.created_at.isoformat(),
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result if task.status == TaskStatus.COMPLETED else None,
            "error": task.error,
            "metadata": task.metadata
        }
    
    async def update_progress(self, task_id: str, progress: float) -> bool:
        """
        Atualiza progresso de uma tarefa.
        
        Args:
            task_id: ID da tarefa
            progress: Progresso (0-100)
        
        Returns:
            True se atualizado, False se tarefa não encontrada
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        
        task.progress = min(max(progress, 0.0), 100.0)
        return True
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancela uma tarefa pendente.
        
        Args:
            task_id: ID da tarefa
        
        Returns:
            True se cancelada, False se não encontrada ou já em execução
        """
        task = self._tasks.get(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return False
        
        task.status = TaskStatus.FAILED
        task.error = "Cancelled by user"
        task.completed_at = datetime.utcnow()
        return True
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """
        Remove tarefas antigas do registro.
        
        Args:
            max_age_hours: Idade máxima em horas
        
        Returns:
            Número de tarefas removidas
        """
        now = datetime.utcnow()
        to_remove = []
        
        async with self._lock:
            for task_id, task in self._tasks.items():
                if task.completed_at:
                    age = (now - task.completed_at).total_seconds() / 3600
                    if age > max_age_hours:
                        to_remove.append(task_id)
            
            for task_id in to_remove:
                del self._tasks[task_id]
        
        if to_remove:
            logger.info(f"Limpeza: {len(to_remove)} tarefas antigas removidas")
        
        return len(to_remove)
    
    async def list_tasks(
        self,
        status_filter: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> list[Dict[str, Any]]:
        """
        Lista tarefas registradas.
        
        Args:
            status_filter: Filtrar por status
            limit: Limite de resultados
        
        Returns:
            Lista de tarefas
        """
        tasks = []
        for task in list(self._tasks.values())[-limit:]:
            if status_filter is None or task.status == status_filter:
                tasks.append({
                    "task_id": task.id,
                    "status": task.status.value,
                    "progress": task.progress,
                    "created_at": task.created_at.isoformat(),
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "metadata": task.metadata
                })
        return tasks
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Estatísticas do gerenciador de tarefas."""
        status_counts = {s.value: 0 for s in TaskStatus}
        for task in self._tasks.values():
            status_counts[task.status.value] += 1
        
        return {
            "total_tasks": len(self._tasks),
            "by_status": status_counts,
            "max_concurrent": self._semaphore._value
        }


# Singleton
_task_manager: Optional[BackgroundTaskManager] = None


def get_task_manager() -> BackgroundTaskManager:
    """Retorna instância singleton do gerenciador de tarefas."""
    global _task_manager
    if _task_manager is None:
        _task_manager = BackgroundTaskManager()
    return _task_manager
