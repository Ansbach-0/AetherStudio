"""
Serviço de cache para áudios e resultados.

Implementa cache em memória e disco para evitar
reprocessamento de áudios idênticos.
"""

import asyncio
import hashlib
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional
from functools import lru_cache
from dataclasses import dataclass, field
from collections import OrderedDict
import threading

from backend.config import get_settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class CacheEntry:
    """Entrada de cache com metadados."""
    value: Any
    created_at: float
    ttl: int
    hits: int = 0


class MemoryCache:
    """
    Cache em memória thread-safe com LRU.
    
    Features:
    - TTL configurável por entrada
    - Limite de tamanho com evicção LRU
    - Thread-safe
    """
    
    def __init__(self, max_size: int = 100, default_ttl: int = 3600):
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self.max_size = max_size
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            # Verificar TTL
            if time.time() - entry.created_at > entry.ttl:
                del self._cache[key]
                return None
            
            # Atualizar hits e mover para o fim (LRU)
            entry.hits += 1
            self._cache.move_to_end(key)
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Define valor no cache."""
        with self._lock:
            # Verificar limite de tamanho
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)  # Remove mais antigo
            
            self._cache[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                ttl=ttl or self.default_ttl
            )
    
    def delete(self, key: str) -> bool:
        """Remove entrada do cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """Limpa todo o cache."""
        with self._lock:
            self._cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Estatísticas do cache."""
        with self._lock:
            total_hits = sum(e.hits for e in self._cache.values())
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "total_hits": total_hits
            }


class AudioCacheService:
    """
    Cache especializado para resultados de processamento de áudio.
    
    Gera hash único baseado em:
    - Texto (para TTS)
    - Áudio de referência (hash do arquivo)
    - Parâmetros de processamento
    """
    
    def __init__(self):
        self.memory_cache = MemoryCache(
            max_size=settings.cache_max_size,
            default_ttl=settings.cache_ttl_seconds
        )
        self.cache_dir = Path(settings.output_dir) / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_key(self, text: str, reference_hash: str, params: Dict) -> str:
        """Gera chave única para cache."""
        content = f"{text}_{reference_hash}_{sorted(params.items())}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _hash_file(self, file_path: str) -> str:
        """Gera hash de arquivo."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    async def get_cached_audio(
        self,
        text: str,
        reference_audio: str,
        params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Busca áudio no cache."""
        try:
            ref_hash = self._hash_file(reference_audio)
            cache_key = self._generate_key(text, ref_hash, params)
            
            # Verificar cache em memória
            result = self.memory_cache.get(cache_key)
            if result:
                logger.debug(f"Cache hit (memória): {cache_key[:8]}")
                return result
            
            # Verificar cache em disco
            cached_file = self.cache_dir / f"{cache_key}.wav"
            if cached_file.exists():
                logger.debug(f"Cache hit (disco): {cache_key[:8]}")
                return {"audio_url": f"/outputs/cache/{cache_key}.wav", "cached": True}
            
            return None
        except Exception as e:
            logger.warning(f"Erro ao buscar cache: {e}")
            return None
    
    async def cache_audio(
        self,
        text: str,
        reference_audio: str,
        params: Dict[str, Any],
        result: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> None:
        """Salva resultado no cache."""
        try:
            ref_hash = self._hash_file(reference_audio)
            cache_key = self._generate_key(text, ref_hash, params)
            
            self.memory_cache.set(cache_key, result, ttl or settings.cache_ttl_seconds)
            logger.debug(f"Resultado cacheado: {cache_key[:8]}")
        except Exception as e:
            logger.warning(f"Erro ao cachear: {e}")
    
    def clear_cache(self) -> Dict[str, Any]:
        """Limpa todos os caches."""
        self.memory_cache.clear()
        # Limpar cache em disco
        import shutil
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        return {"cleared": True}
    
    @property
    def status(self) -> Dict[str, Any]:
        """Retorna status do cache."""
        return {
            "memory_cache": self.memory_cache.stats(),
            "cache_dir": str(self.cache_dir)
        }


# Singleton
_cache_service: Optional[AudioCacheService] = None


def get_cache_service() -> AudioCacheService:
    """Retorna instância singleton do serviço de cache."""
    global _cache_service
    if _cache_service is None:
        _cache_service = AudioCacheService()
    return _cache_service
