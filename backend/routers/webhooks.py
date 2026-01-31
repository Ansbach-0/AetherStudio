"""
Endpoints de gerenciamento de webhooks.

Permite que usuários configurem URLs para receber notificações
de eventos do sistema via HTTP POST.
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field, HttpUrl

from backend.services.webhook_service import (
    WebhookEvent,
    WebhookService,
    get_webhook_service,
)
from backend.utils.logger import get_logger

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
logger = get_logger(__name__)


# =============================================================================
# SCHEMAS
# =============================================================================

class WebhookCreate(BaseModel):
    """Schema para criação de webhook."""
    url: HttpUrl = Field(..., description="URL que receberá os eventos via POST")
    events: List[str] = Field(
        ...,
        min_length=1,
        description="Lista de eventos para disparar o webhook"
    )
    secret: Optional[str] = Field(
        None,
        min_length=16,
        max_length=256,
        description="Chave secreta para assinatura HMAC (mínimo 16 caracteres)"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://seu-servidor.com/webhook",
                    "events": ["task.completed", "voice.clone.completed"],
                    "secret": "sua-chave-secreta-segura"
                }
            ]
        }
    }


class WebhookResponse(BaseModel):
    """Schema de resposta de webhook."""
    id: str
    user_id: int
    url: str
    events: List[str]
    active: bool
    has_secret: bool
    failure_count: int
    created_at: str
    last_triggered_at: Optional[str] = None


class WebhookListResponse(BaseModel):
    """Schema de listagem de webhooks."""
    webhooks: List[WebhookResponse]
    total: int


class WebhookTestResponse(BaseModel):
    """Schema de resposta de teste de webhook."""
    success: bool
    webhook_id: str
    status_code: Optional[int] = None
    response_body: Optional[str] = None
    error: Optional[str] = None
    duration_ms: int


class AvailableEventsResponse(BaseModel):
    """Schema de eventos disponíveis."""
    events: List[dict]


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(
    "",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar webhook",
    description="Registra um novo webhook para receber notificações de eventos."
)
async def create_webhook(
    webhook_data: WebhookCreate,
    user_id: int = Query(..., description="ID do usuário")
) -> WebhookResponse:
    """
    Cria um novo webhook.
    
    O webhook receberá requisições POST na URL especificada
    sempre que um dos eventos configurados ocorrer.
    
    Se um secret for fornecido, todas as requisições incluirão
    um header X-Webhook-Signature com assinatura HMAC-SHA256.
    
    Args:
        webhook_data: Dados do webhook a criar
        user_id: ID do usuário dono do webhook
    
    Returns:
        WebhookResponse: Webhook criado
    """
    service = get_webhook_service()
    webhook_id = str(uuid.uuid4())
    
    try:
        webhook = service.register_webhook(
            webhook_id=webhook_id,
            user_id=user_id,
            url=str(webhook_data.url),
            events=webhook_data.events,
            secret=webhook_data.secret
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    logger.info(f"Webhook criado: {webhook_id} para usuário {user_id}")
    
    return WebhookResponse(
        id=webhook.id,
        user_id=webhook.user_id,
        url=webhook.url,
        events=webhook.events,
        active=webhook.active,
        has_secret=webhook.secret is not None,
        failure_count=webhook.failure_count,
        created_at=webhook.created_at.isoformat(),
        last_triggered_at=webhook.last_triggered_at.isoformat() if webhook.last_triggered_at else None
    )


@router.get(
    "",
    response_model=WebhookListResponse,
    summary="Listar webhooks",
    description="Lista todos os webhooks do usuário."
)
async def list_webhooks(
    user_id: int = Query(..., description="ID do usuário")
) -> WebhookListResponse:
    """
    Lista webhooks do usuário.
    
    Args:
        user_id: ID do usuário
    
    Returns:
        WebhookListResponse: Lista de webhooks
    """
    service = get_webhook_service()
    webhooks = service.get_user_webhooks(user_id)
    
    return WebhookListResponse(
        webhooks=[
            WebhookResponse(
                id=wh.id,
                user_id=wh.user_id,
                url=wh.url,
                events=wh.events,
                active=wh.active,
                has_secret=wh.secret is not None,
                failure_count=wh.failure_count,
                created_at=wh.created_at.isoformat(),
                last_triggered_at=wh.last_triggered_at.isoformat() if wh.last_triggered_at else None
            )
            for wh in webhooks
        ],
        total=len(webhooks)
    )


@router.get(
    "/events",
    response_model=AvailableEventsResponse,
    summary="Listar eventos disponíveis",
    description="Lista todos os tipos de eventos que podem disparar webhooks."
)
async def list_available_events() -> AvailableEventsResponse:
    """
    Lista eventos disponíveis para webhooks.
    
    Returns:
        AvailableEventsResponse: Lista de eventos
    """
    events = [
        {
            "name": event.value,
            "description": _get_event_description(event)
        }
        for event in WebhookEvent
    ]
    
    return AvailableEventsResponse(events=events)


@router.get(
    "/{webhook_id}",
    response_model=WebhookResponse,
    summary="Obter webhook",
    description="Retorna detalhes de um webhook específico."
)
async def get_webhook(
    webhook_id: str,
    user_id: int = Query(..., description="ID do usuário")
) -> WebhookResponse:
    """
    Busca webhook por ID.
    
    Args:
        webhook_id: ID do webhook
        user_id: ID do usuário (para verificar permissão)
    
    Returns:
        WebhookResponse: Dados do webhook
    """
    service = get_webhook_service()
    webhook = service.get_webhook(webhook_id)
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook não encontrado"
        )
    
    if webhook.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a este webhook"
        )
    
    return WebhookResponse(
        id=webhook.id,
        user_id=webhook.user_id,
        url=webhook.url,
        events=webhook.events,
        active=webhook.active,
        has_secret=webhook.secret is not None,
        failure_count=webhook.failure_count,
        created_at=webhook.created_at.isoformat(),
        last_triggered_at=webhook.last_triggered_at.isoformat() if webhook.last_triggered_at else None
    )


@router.delete(
    "/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover webhook",
    description="Remove um webhook do usuário."
)
async def delete_webhook(
    webhook_id: str,
    user_id: int = Query(..., description="ID do usuário")
):
    """
    Remove um webhook.
    
    Args:
        webhook_id: ID do webhook a remover
        user_id: ID do usuário (para verificar permissão)
    """
    service = get_webhook_service()
    webhook = service.get_webhook(webhook_id)
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook não encontrado"
        )
    
    if webhook.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a este webhook"
        )
    
    service.delete_webhook(webhook_id)
    logger.info(f"Webhook removido: {webhook_id}")


@router.post(
    "/{webhook_id}/test",
    response_model=WebhookTestResponse,
    summary="Testar webhook",
    description="Envia uma requisição de teste para o webhook."
)
async def test_webhook(
    webhook_id: str,
    user_id: int = Query(..., description="ID do usuário")
) -> WebhookTestResponse:
    """
    Envia evento de teste para o webhook.
    
    Útil para verificar se a URL está configurada corretamente
    e recebendo as requisições.
    
    Args:
        webhook_id: ID do webhook a testar
        user_id: ID do usuário (para verificar permissão)
    
    Returns:
        WebhookTestResponse: Resultado do teste
    """
    service = get_webhook_service()
    webhook = service.get_webhook(webhook_id)
    
    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook não encontrado"
        )
    
    if webhook.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado a este webhook"
        )
    
    # Temporariamente adicionar evento de teste se não configurado
    original_events = webhook.events.copy()
    test_event = "task.completed"
    
    if test_event not in webhook.events:
        webhook.events.append(test_event)
    
    # Enviar evento de teste
    result = await service.send_webhook(
        webhook_id=webhook_id,
        event=test_event,
        data={
            "test": True,
            "message": "Este é um evento de teste do webhook",
            "webhook_id": webhook_id
        }
    )
    
    # Restaurar eventos originais
    webhook.events = original_events
    
    logger.info(f"Teste de webhook: {webhook_id}, success={result.success}")
    
    return WebhookTestResponse(
        success=result.success,
        webhook_id=result.webhook_id,
        status_code=result.status_code,
        response_body=result.response_body,
        error=result.error,
        duration_ms=result.duration_ms
    )


# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def _get_event_description(event: WebhookEvent) -> str:
    """Retorna descrição de um evento."""
    descriptions = {
        WebhookEvent.TASK_COMPLETED: "Disparado quando uma task é concluída com sucesso",
        WebhookEvent.TASK_FAILED: "Disparado quando uma task falha",
        WebhookEvent.VOICE_CLONE_COMPLETED: "Disparado quando clonagem de voz é concluída",
        WebhookEvent.VOICE_CONVERT_COMPLETED: "Disparado quando conversão de voz é concluída",
        WebhookEvent.TRAINING_STARTED: "Disparado quando um treinamento é iniciado",
        WebhookEvent.TRAINING_COMPLETED: "Disparado quando um treinamento é concluído",
        WebhookEvent.TRAINING_FAILED: "Disparado quando um treinamento falha",
        WebhookEvent.CREDITS_LOW: "Disparado quando créditos ficam abaixo do limite",
        WebhookEvent.PAYMENT_RECEIVED: "Disparado quando um pagamento é confirmado",
    }
    return descriptions.get(event, "Evento do sistema")
