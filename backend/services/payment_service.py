"""
Serviço de pagamentos com Mercado Pago.

Implementação placeholder preparada para integração futura.
Se API key não configurada, retorna status de manutenção.
"""

from typing import Any, Dict, List, Optional

from backend.config import get_settings
from backend.utils.logger import get_logger

# Import condicional do SDK Mercado Pago
try:
    import mercadopago
    MP_SDK_AVAILABLE = True
except ImportError:
    MP_SDK_AVAILABLE = False
    mercadopago = None

logger = get_logger(__name__)
settings = get_settings()


class PaymentService:
    """
    Serviço de pagamentos.
    
    Gerencia integração com Mercado Pago para compra de créditos.
    Quando não configurado, opera em modo placeholder.
    """
    
    # Planos disponíveis
    PLANS: Dict[str, Dict[str, Any]] = {
        "free": {
            "name": "Free",
            "credits": 100,
            "price_brl": 0.0,
            "max_voices": 5,
            "features": ["basic_cloning", "3_languages"],
            "description": "Perfeito para testar a plataforma"
        },
        "basic": {
            "name": "Basic",
            "credits": 1000,
            "price_brl": 29.90,
            "max_voices": 20,
            "features": ["basic_cloning", "emotion_control", "5_languages", "api_access"],
            "description": "Ideal para criadores iniciantes"
        },
        "pro": {
            "name": "Pro",
            "credits": 5000,
            "price_brl": 99.90,
            "max_voices": 100,
            "features": ["all_features", "custom_rvc_training", "priority_support"],
            "description": "Para criadores profissionais"
        },
        "enterprise": {
            "name": "Enterprise",
            "credits": 25000,
            "price_brl": 399.90,
            "max_voices": -1,  # Ilimitado
            "features": ["all_features", "custom_rvc_training", "dedicated_support", "custom_limits"],
            "description": "Solução corporativa personalizada"
        }
    }
    
    # Pacotes de créditos avulsos
    CREDIT_PACKAGES: List[Dict[str, Any]] = [
        {"credits": 500, "price_brl": 19.90, "bonus": 0},
        {"credits": 1000, "price_brl": 34.90, "bonus": 50},
        {"credits": 2500, "price_brl": 79.90, "bonus": 150},
        {"credits": 5000, "price_brl": 149.90, "bonus": 500},
        {"credits": 10000, "price_brl": 279.90, "bonus": 1500},
    ]
    
    def __init__(self) -> None:
        """Inicializa o serviço de pagamentos."""
        self.mp_client: Any = None
        self.is_configured: bool = False
        self._setup_client()
    
    def _setup_client(self) -> None:
        """Configura cliente Mercado Pago se disponível."""
        mp_access_token = getattr(settings, 'mercadopago_access_token', None)
        
        if not mp_access_token or mp_access_token == "":
            logger.warning("=" * 60)
            logger.warning("🚧 MODO MANUTENÇÃO: Sistema de pagamentos desativado")
            logger.warning("   Mercado Pago Access Token não configurado")
            logger.warning("   Configure MERCADOPAGO_ACCESS_TOKEN no .env para ativar")
            logger.warning("=" * 60)
            return
        
        if not MP_SDK_AVAILABLE:
            logger.warning("=" * 60)
            logger.warning("🚧 MODO MANUTENÇÃO: SDK Mercado Pago não instalado")
            logger.warning("   Execute: pip install mercadopago")
            logger.warning("=" * 60)
            return
        
        try:
            self.mp_client = mercadopago.SDK(mp_access_token)
            self.is_configured = True
            logger.info("Mercado Pago configurado com sucesso")
        except Exception as e:
            logger.error(f"Erro ao configurar Mercado Pago: {e}")
    
    def is_available(self) -> bool:
        """
        Verifica se pagamentos estão disponíveis.
        
        Returns:
            bool: True se o sistema de pagamentos está operacional
        """
        return self.is_configured and self.mp_client is not None
    
    def get_maintenance_message(self) -> Dict[str, Any]:
        """
        Retorna mensagem de manutenção.
        
        Returns:
            Dict com informações sobre o status de manutenção
        """
        return {
            "available": False,
            "status": "maintenance",
            "message": "🚧 Sistema de pagamentos em manutenção",
            "description": "Estamos trabalhando para disponibilizar os pagamentos em breve!",
            "contact": "Entre em contato para adquirir créditos: contato@voiceclone.com"
        }
    
    async def create_payment(
        self,
        user_id: int,
        plan_id: Optional[str] = None,
        credits_package_index: Optional[int] = None,
        success_url: Optional[str] = None,
        failure_url: Optional[str] = None,
        pending_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria pagamento via Mercado Pago.
        
        Args:
            user_id: ID do usuário
            plan_id: ID do plano (se for upgrade de plano)
            credits_package_index: Índice do pacote de créditos (se for compra avulsa)
            success_url: URL de redirecionamento em caso de sucesso
            failure_url: URL de redirecionamento em caso de falha
            pending_url: URL de redirecionamento em caso de pagamento pendente
        
        Returns:
            Dict com dados do pagamento ou mensagem de manutenção
        """
        if not self.is_available():
            return self.get_maintenance_message()
        
        # Determinar item e valor
        if plan_id and plan_id in self.PLANS:
            item = self.PLANS[plan_id]
            title = f"Plano {item['name']} - Voice Cloning SaaS"
            price = item['price_brl']
            credits = item['credits']
        elif credits_package_index is not None and 0 <= credits_package_index < len(self.CREDIT_PACKAGES):
            item = self.CREDIT_PACKAGES[credits_package_index]
            credits = item['credits'] + item['bonus']
            title = f"Pacote de {credits} créditos - Voice Cloning SaaS"
            price = item['price_brl']
        else:
            return {
                "error": "invalid_item",
                "message": "Plano ou pacote de créditos inválido"
            }
        
        if price <= 0:
            return {
                "error": "free_item",
                "message": "Este item é gratuito e não requer pagamento"
            }
        
        try:
            # Criar preferência de pagamento no Mercado Pago
            preference_data = {
                "items": [
                    {
                        "title": title,
                        "quantity": 1,
                        "unit_price": float(price),
                        "currency_id": "BRL"
                    }
                ],
                "external_reference": f"user_{user_id}_credits_{credits}",
                "back_urls": {
                    "success": success_url or "https://voiceclone.com/payment/success",
                    "failure": failure_url or "https://voiceclone.com/payment/failure",
                    "pending": pending_url or "https://voiceclone.com/payment/pending"
                },
                "auto_return": "approved",
                "notification_url": "https://voiceclone.com/api/v1/payment/webhook/mercadopago",
                "metadata": {
                    "user_id": user_id,
                    "credits": credits,
                    "plan_id": plan_id
                }
            }
            
            preference_response = self.mp_client.preference().create(preference_data)
            preference = preference_response.get("response", {})
            
            return {
                "success": True,
                "payment_id": preference.get("id"),
                "init_point": preference.get("init_point"),  # URL de pagamento
                "sandbox_init_point": preference.get("sandbox_init_point"),
                "external_reference": preference_data["external_reference"],
                "amount": price,
                "credits": credits
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar pagamento: {e}")
            return {
                "error": "payment_error",
                "message": "Erro ao processar pagamento. Tente novamente."
            }
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Verifica status de um pagamento.
        
        Args:
            payment_id: ID do pagamento no Mercado Pago
        
        Returns:
            Dict com status do pagamento ou mensagem de manutenção
        """
        if not self.is_available():
            return self.get_maintenance_message()
        
        try:
            payment_response = self.mp_client.payment().get(payment_id)
            payment = payment_response.get("response", {})
            
            return {
                "success": True,
                "payment_id": payment.get("id"),
                "status": payment.get("status"),
                "status_detail": payment.get("status_detail"),
                "amount": payment.get("transaction_amount"),
                "external_reference": payment.get("external_reference"),
                "date_created": payment.get("date_created"),
                "date_approved": payment.get("date_approved")
            }
            
        except Exception as e:
            logger.error(f"Erro ao consultar pagamento: {e}")
            return {
                "error": "query_error",
                "message": "Erro ao consultar pagamento."
            }
    
    async def handle_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa webhook do Mercado Pago.
        
        Chamado automaticamente pelo Mercado Pago quando há
        atualizações no status de pagamentos.
        
        Args:
            data: Dados do webhook enviados pelo Mercado Pago
        
        Returns:
            Dict com resultado do processamento
        """
        if not self.is_available():
            return {"status": "maintenance", "processed": False}
        
        try:
            webhook_type = data.get("type")
            webhook_data = data.get("data", {})
            
            if webhook_type == "payment":
                payment_id = webhook_data.get("id")
                
                if payment_id:
                    # Buscar detalhes do pagamento
                    payment_status = await self.get_payment_status(str(payment_id))
                    
                    if payment_status.get("status") == "approved":
                        # Pagamento aprovado - processar créditos
                        external_ref = payment_status.get("external_reference", "")
                        
                        # Parse do external_reference: "user_{user_id}_credits_{credits}"
                        parts = external_ref.split("_")
                        if len(parts) >= 4:
                            user_id = int(parts[1])
                            credits = int(parts[3])
                            
                            # TODO: Adicionar créditos ao usuário
                            # await credits_service.add_credits(user_id, credits, "purchase")
                            
                            logger.info(f"Pagamento aprovado: {credits} créditos para usuário {user_id}")
                            
                            return {
                                "status": "success",
                                "processed": True,
                                "user_id": user_id,
                                "credits_added": credits
                            }
                    
                    return {
                        "status": payment_status.get("status"),
                        "processed": True
                    }
            
            return {"status": "ignored", "processed": False, "type": webhook_type}
            
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {e}")
            return {"status": "error", "processed": False, "error": str(e)}
    
    def get_plans(self) -> List[Dict[str, Any]]:
        """
        Retorna lista de planos disponíveis.
        
        Returns:
            Lista de planos com seus detalhes
        """
        return [
            {"id": plan_id, **plan_data}
            for plan_id, plan_data in self.PLANS.items()
        ]
    
    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Retorna detalhes de um plano específico.
        
        Args:
            plan_id: ID do plano
        
        Returns:
            Dict com detalhes do plano ou None se não existe
        """
        if plan_id in self.PLANS:
            return {"id": plan_id, **self.PLANS[plan_id]}
        return None
    
    def get_credit_packages(self) -> List[Dict[str, Any]]:
        """
        Retorna pacotes de créditos disponíveis.
        
        Returns:
            Lista de pacotes de créditos
        """
        return [
            {"index": i, **package}
            for i, package in enumerate(self.CREDIT_PACKAGES)
        ]
    
    @property
    def status(self) -> Dict[str, Any]:
        """
        Retorna status do serviço de pagamentos.
        
        Returns:
            Dict com informações sobre o status do serviço
        """
        return {
            "available": self.is_available(),
            "sdk_installed": MP_SDK_AVAILABLE,
            "configured": self.is_configured,
            "mode": "live" if self.is_available() else "maintenance"
        }


# Instância singleton do serviço
_payment_service: Optional[PaymentService] = None


def get_payment_service() -> PaymentService:
    """
    Retorna instância singleton do serviço de pagamentos.
    
    Returns:
        PaymentService: Instância do serviço
    """
    global _payment_service
    if _payment_service is None:
        _payment_service = PaymentService()
    return _payment_service
