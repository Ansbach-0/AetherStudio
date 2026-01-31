"""
Módulo de middlewares.

Contém middlewares para rate limiting, logging de requisições
e outras funcionalidades transversais.
"""

from backend.middleware.rate_limiter import limiter

__all__ = ["limiter"]
