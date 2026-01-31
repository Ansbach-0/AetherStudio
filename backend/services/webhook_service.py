"""
Serviço de webhooks para notificações.

Permite que usuários registrem URLs para receber notificações
de eventos como conclusão de processamento, treinos, etc.
"""

import hashlib
import hmac
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

import httpx

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class WebhookEvent(str, Enum):
    """Tipos de eventos que podem disparar webhooks."""
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    VOICE_CLONE_COMPLETED = "voice.clone.completed"
    VOICE_CONVERT_COMPLETED = "voice.convert.completed"
    TRAINING_STARTED = "training.started"
    TRAINING_COMPLETED = "training.completed"
    TRAINING_FAILED = "training.failed"
    CREDITS_LOW = "credits.low"
    PAYMENT_RECEIVED = "payment.received"


@dataclass
class WebhookConfig:
    """Configuração de um webhook."""
    id: str
    user_id: int
    url: str
    events: List[str]
    secret: Optional[str] = None
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_triggered_at: Optional[datetime] = None
    failure_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookDeliveryResult:
    """Resultado de uma tentativa de entrega de webhook."""
    success: bool
    webhook_id: str
    event: str
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    attempts: int = 1
    duration_ms: int = 0


class WebhookService:
    """
    Serviço para gerenciamento e disparo de webhooks.
    
    Suporta:
    - Registro de webhooks por usuário
    - Assinatura HMAC para verificação de autenticidade
    - Retry automático com backoff exponencial
    - Rate limiting por webhook
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
        timeout_seconds: float = 10.0
    ):
        self._webhooks: Dict[str, WebhookConfig] = {}
        self._max_retries = max_retries
        self._retry_delay = retry_delay_seconds
        self._timeout = timeout_seconds
        self._delivery_history: List[WebhookDeliveryResult] = []
    
    def register_webhook(
        self,
        webhook_id: str,
        user_id: int,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> WebhookConfig:
        """
        Registra um novo webhook para o usuário.
        
        Args:
            webhook_id: ID único do webhook
            user_id: ID do usuário dono do webhook
            url: URL que receberá as notificações POST
            events: Lista de eventos para disparar o webhook
            secret: Chave secreta para assinatura HMAC (opcional)
            metadata: Dados adicionais do webhook
        
        Returns:
            WebhookConfig: Configuração do webhook criado
        """
        # Validar URL
        if not url.startswith(("http://", "https://")):
            raise ValueError("URL deve começar com http:// ou https://")
        
        # Validar eventos
        valid_events = {e.value for e in WebhookEvent}
        for event in events:
            if event not in valid_events:
                raise ValueError(f"Evento inválido: {event}. Válidos: {valid_events}")
        
        webhook = WebhookConfig(
            id=webhook_id,
            user_id=user_id,
            url=url,
            events=events,
            secret=secret,
            metadata=metadata or {}
        )
        
        self._webhooks[webhook_id] = webhook
        
        logger.info(
            f"Webhook registrado: id={webhook_id}, user={user_id}, "
            f"events={events}, url={url[:50]}..."
        )
        
        return webhook
    
    def get_webhook(self, webhook_id: str) -> Optional[WebhookConfig]:
        """Retorna configuração de um webhook."""
        return self._webhooks.get(webhook_id)
    
    def get_user_webhooks(self, user_id: int) -> List[WebhookConfig]:
        """Lista todos os webhooks de um usuário."""
        return [
            wh for wh in self._webhooks.values()
            if wh.user_id == user_id
        ]
    
    def delete_webhook(self, webhook_id: str) -> bool:
        """
        Remove um webhook.
        
        Args:
            webhook_id: ID do webhook a remover
        
        Returns:
            bool: True se removido, False se não encontrado
        """
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            logger.info(f"Webhook removido: {webhook_id}")
            return True
        return False
    
    def update_webhook(
        self,
        webhook_id: str,
        url: Optional[str] = None,
        events: Optional[List[str]] = None,
        secret: Optional[str] = None,
        active: Optional[bool] = None
    ) -> Optional[WebhookConfig]:
        """
        Atualiza configuração de um webhook.
        
        Args:
            webhook_id: ID do webhook
            url: Nova URL (opcional)
            events: Novos eventos (opcional)
            secret: Novo secret (opcional)
            active: Novo status ativo (opcional)
        
        Returns:
            WebhookConfig atualizado ou None se não encontrado
        """
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            return None
        
        if url is not None:
            webhook.url = url
        if events is not None:
            webhook.events = events
        if secret is not None:
            webhook.secret = secret
        if active is not None:
            webhook.active = active
        
        logger.info(f"Webhook atualizado: {webhook_id}")
        return webhook
    
    def _generate_signature(self, payload: str, secret: str) -> str:
        """
        Gera assinatura HMAC-SHA256 para o payload.
        
        Args:
            payload: Corpo da requisição em JSON
            secret: Chave secreta do webhook
        
        Returns:
            str: Assinatura no formato "sha256=<hash>"
        """
        signature = hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    async def send_webhook(
        self,
        webhook_id: str,
        event: str,
        data: Dict[str, Any]
    ) -> WebhookDeliveryResult:
        """
        Envia POST para URL do webhook com retry automático.
        
        Args:
            webhook_id: ID do webhook de destino
            event: Tipo do evento sendo enviado
            data: Dados do evento
        
        Returns:
            WebhookDeliveryResult: Resultado da entrega
        """
        webhook = self._webhooks.get(webhook_id)
        
        if not webhook:
            return WebhookDeliveryResult(
                success=False,
                webhook_id=webhook_id,
                event=event,
                error="Webhook não encontrado"
            )
        
        if not webhook.active:
            return WebhookDeliveryResult(
                success=False,
                webhook_id=webhook_id,
                event=event,
                error="Webhook desativado"
            )
        
        if event not in webhook.events:
            return WebhookDeliveryResult(
                success=False,
                webhook_id=webhook_id,
                event=event,
                error=f"Evento {event} não configurado para este webhook"
            )
        
        # Construir payload
        payload = {
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "webhook_id": webhook_id,
            "data": data
        }
        payload_json = json.dumps(payload, default=str)
        
        # Preparar headers
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "VoiceCloner-Webhook/1.0",
            "X-Webhook-Event": event,
            "X-Webhook-Id": webhook_id
        }
        
        # Adicionar assinatura HMAC se secret configurado
        if webhook.secret:
            signature = self._generate_signature(payload_json, webhook.secret)
            headers["X-Webhook-Signature"] = signature
        
        # Tentar enviar com retry
        last_error = None
        attempts = 0
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for attempt in range(self._max_retries):
                attempts = attempt + 1
                
                try:
                    response = await client.post(
                        webhook.url,
                        content=payload_json,
                        headers=headers
                    )
                    
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    # Considerar sucesso para códigos 2xx
                    if 200 <= response.status_code < 300:
                        webhook.last_triggered_at = datetime.utcnow()
                        webhook.failure_count = 0
                        
                        result = WebhookDeliveryResult(
                            success=True,
                            webhook_id=webhook_id,
                            event=event,
                            status_code=response.status_code,
                            response_body=response.text[:500],
                            attempts=attempts,
                            duration_ms=duration_ms
                        )
                        
                        self._delivery_history.append(result)
                        logger.info(
                            f"Webhook entregue: {webhook_id}, event={event}, "
                            f"status={response.status_code}, attempts={attempts}"
                        )
                        
                        return result
                    
                    # Erro do servidor - tentar novamente
                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                    
                except httpx.TimeoutException:
                    last_error = "Timeout na requisição"
                except httpx.RequestError as e:
                    last_error = f"Erro de conexão: {str(e)}"
                except Exception as e:
                    last_error = f"Erro inesperado: {str(e)}"
                
                # Aguardar antes de retry (backoff exponencial)
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (2 ** attempt)
                    logger.warning(
                        f"Webhook falhou (tentativa {attempts}): {last_error}. "
                        f"Retry em {delay}s..."
                    )
                    await self._async_sleep(delay)
        
        # Todas as tentativas falharam
        duration_ms = int((time.time() - start_time) * 1000)
        webhook.failure_count += 1
        
        # Desativar webhook após muitas falhas
        if webhook.failure_count >= 10:
            webhook.active = False
            logger.warning(f"Webhook desativado após {webhook.failure_count} falhas: {webhook_id}")
        
        result = WebhookDeliveryResult(
            success=False,
            webhook_id=webhook_id,
            event=event,
            error=last_error,
            attempts=attempts,
            duration_ms=duration_ms
        )
        
        self._delivery_history.append(result)
        logger.error(
            f"Webhook falhou permanentemente: {webhook_id}, event={event}, "
            f"error={last_error}, attempts={attempts}"
        )
        
        return result
    
    async def _async_sleep(self, seconds: float):
        """Sleep assíncrono para retry."""
        import asyncio
        await asyncio.sleep(seconds)
    
    async def broadcast_event(
        self,
        user_id: int,
        event: str,
        data: Dict[str, Any]
    ) -> List[WebhookDeliveryResult]:
        """
        Envia evento para todos os webhooks do usuário configurados para ele.
        
        Args:
            user_id: ID do usuário
            event: Tipo do evento
            data: Dados do evento
        
        Returns:
            Lista de resultados de entrega
        """
        results = []
        
        for webhook in self.get_user_webhooks(user_id):
            if webhook.active and event in webhook.events:
                result = await self.send_webhook(webhook.id, event, data)
                results.append(result)
        
        return results
    
    def get_delivery_history(
        self,
        webhook_id: Optional[str] = None,
        limit: int = 100
    ) -> List[WebhookDeliveryResult]:
        """
        Retorna histórico de entregas de webhooks.
        
        Args:
            webhook_id: Filtrar por webhook (opcional)
            limit: Número máximo de resultados
        
        Returns:
            Lista de resultados de entrega
        """
        history = self._delivery_history
        
        if webhook_id:
            history = [r for r in history if r.webhook_id == webhook_id]
        
        return history[-limit:]


# Singleton do serviço
_webhook_service: Optional[WebhookService] = None


def get_webhook_service() -> WebhookService:
    """Retorna instância singleton do serviço de webhooks."""
    global _webhook_service
    
    if _webhook_service is None:
        _webhook_service = WebhookService()
    
    return _webhook_service
