"""
Módulo de routers da API.

Contém todos os endpoints organizados por domínio.
"""

from backend.routers import health, payment, user, voice, tasks, webhooks

__all__ = ["health", "payment", "user", "voice", "tasks", "webhooks"]
