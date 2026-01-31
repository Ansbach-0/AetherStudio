"""
Endpoints de pagamento e planos.

Fornece API para consulta de planos, compra de créditos
e webhooks de pagamento.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request, status

from backend.models.schemas import (
    CreditPackageResponse,
    PaymentStatusResponse,
    PlanResponse,
)
from backend.services.payment_service import get_payment_service
from backend.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/payment", tags=["Payment"])


@router.get(
    "/status",
    response_model=PaymentStatusResponse,
    summary="Status do sistema de pagamentos",
    description="Verifica se o sistema de pagamentos está disponível ou em manutenção."
)
async def get_payment_system_status():
    """
    Retorna status do sistema de pagamentos.
    
    Se o Mercado Pago não estiver configurado, retorna status de manutenção.
    """
    payment_service = get_payment_service()
    
    if not payment_service.is_available():
        maintenance = payment_service.get_maintenance_message()
        return PaymentStatusResponse(
            available=maintenance["available"],
            status=maintenance["status"],
            message=maintenance["message"],
            description=maintenance["description"]
        )
    
    return PaymentStatusResponse(
        available=True,
        status="live",
        message="Sistema de pagamentos operacional",
        description="Pagamentos via Mercado Pago disponíveis"
    )


@router.get(
    "/plans",
    summary="Lista planos disponíveis",
    description="Retorna todos os planos de assinatura com seus benefícios e preços."
)
async def list_plans():
    """
    Lista planos disponíveis.
    
    Retorna todos os planos (free, basic, pro, enterprise)
    com informações de preço, créditos e recursos.
    """
    payment_service = get_payment_service()
    
    return {
        "plans": payment_service.get_plans(),
        "payment_available": payment_service.is_available(),
        "currency": "BRL"
    }


@router.get(
    "/plans/{plan_id}",
    summary="Detalhes de um plano",
    description="Retorna informações detalhadas de um plano específico."
)
async def get_plan(plan_id: str):
    """
    Retorna detalhes de um plano específico.
    
    Args:
        plan_id: Identificador do plano (free, basic, pro, enterprise)
    """
    payment_service = get_payment_service()
    plan = payment_service.get_plan(plan_id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plano '{plan_id}' não encontrado"
        )
    
    return {
        "plan": plan,
        "payment_available": payment_service.is_available()
    }


@router.get(
    "/credits/packages",
    summary="Lista pacotes de créditos",
    description="Retorna todos os pacotes de créditos avulsos disponíveis para compra."
)
async def list_credit_packages():
    """
    Lista pacotes de créditos disponíveis.
    
    Cada pacote pode incluir bônus de créditos extras.
    """
    payment_service = get_payment_service()
    
    return {
        "packages": payment_service.get_credit_packages(),
        "payment_available": payment_service.is_available(),
        "currency": "BRL"
    }


@router.post(
    "/checkout",
    summary="Iniciar checkout",
    description="Inicia processo de compra de plano ou pacote de créditos."
)
async def create_checkout(
    plan_id: Optional[str] = Query(None, description="ID do plano para upgrade"),
    package_index: Optional[int] = Query(None, description="Índice do pacote de créditos"),
    user_id: int = Query(..., description="ID do usuário"),
    success_url: Optional[str] = Query(None, description="URL de retorno em caso de sucesso"),
    failure_url: Optional[str] = Query(None, description="URL de retorno em caso de falha")
):
    """
    Inicia processo de compra.
    
    Deve fornecer plan_id OU package_index, não ambos.
    
    Se o sistema de pagamentos não estiver disponível,
    retorna mensagem de manutenção.
    """
    payment_service = get_payment_service()
    
    if not payment_service.is_available():
        return payment_service.get_maintenance_message()
    
    # Validar entrada
    if plan_id is None and package_index is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forneça plan_id ou package_index"
        )
    
    if plan_id is not None and package_index is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forneça apenas plan_id OU package_index, não ambos"
        )
    
    # Criar pagamento
    result = await payment_service.create_payment(
        user_id=user_id,
        plan_id=plan_id,
        credits_package_index=package_index,
        success_url=success_url,
        failure_url=failure_url
    )
    
    return result


@router.get(
    "/checkout/{payment_id}",
    summary="Status do pagamento",
    description="Verifica o status atual de um pagamento."
)
async def check_payment_status(payment_id: str):
    """
    Verifica status de um pagamento específico.
    
    Args:
        payment_id: ID do pagamento no Mercado Pago
    """
    payment_service = get_payment_service()
    
    if not payment_service.is_available():
        return payment_service.get_maintenance_message()
    
    result = await payment_service.get_payment_status(payment_id)
    return result


@router.post(
    "/webhook/mercadopago",
    summary="Webhook Mercado Pago",
    description="Endpoint para receber notificações do Mercado Pago.",
    include_in_schema=False  # Ocultar da documentação pública
)
async def mercadopago_webhook(request: Request):
    """
    Recebe webhooks do Mercado Pago.
    
    Este endpoint é chamado automaticamente pelo Mercado Pago
    quando há atualizações em pagamentos.
    """
    payment_service = get_payment_service()
    
    try:
        data = await request.json()
        logger.info(f"Webhook Mercado Pago recebido: {data.get('type', 'unknown')}")
        
        result = await payment_service.handle_webhook(data)
        return result
        
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}")
        return {"status": "error", "message": str(e)}


@router.get(
    "/service-info",
    summary="Informações do serviço",
    description="Retorna informações técnicas sobre o serviço de pagamentos."
)
async def get_service_info():
    """
    Retorna informações técnicas do serviço de pagamentos.
    
    Útil para debugging e verificação de configuração.
    """
    payment_service = get_payment_service()
    
    return {
        "service": "payment",
        "provider": "Mercado Pago",
        **payment_service.status
    }
