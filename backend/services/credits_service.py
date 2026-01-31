"""
Serviço de gerenciamento de créditos.

Responsável por controlar saldo, cobranças e histórico
de transações de créditos dos usuários.
"""

import json
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.models.entities import OperationType, Transaction, User
from backend.utils.exceptions import InsufficientCreditsError, UserNotFoundError
from backend.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class CreditsService:
    """
    Serviço de gerenciamento de créditos.
    
    Controla todas as operações relacionadas a créditos:
    consultas, débitos, créditos e histórico.
    
    Attributes:
        credits_per_second: Custo por segundo de áudio processado
        min_charge: Cobrança mínima por operação
    """
    
    def __init__(self):
        """Inicializa o serviço de créditos."""
        self.credits_per_second = settings.credits_per_second
        self.min_charge = 1.0  # Cobrança mínima
        
        logger.info(
            f"CreditsService inicializado: "
            f"custo/segundo={self.credits_per_second}"
        )
    
    async def get_balance(
        self,
        db: AsyncSession,
        user_id: int
    ) -> float:
        """
        Consulta saldo de créditos do usuário.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
        
        Returns:
            float: Saldo atual de créditos
        
        Raises:
            UserNotFoundError: Se usuário não existe
        """
        result = await db.execute(
            select(User.credits).where(User.id == user_id)
        )
        balance = result.scalar_one_or_none()
        
        if balance is None:
            raise UserNotFoundError(user_id)
        
        return balance
    
    async def check_credits(
        self,
        db: AsyncSession,
        user_id: int,
        required_amount: float
    ) -> bool:
        """
        Verifica se usuário tem créditos suficientes.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            required_amount: Quantidade necessária
        
        Returns:
            bool: True se tem créditos suficientes
        """
        balance = await self.get_balance(db, user_id)
        return balance >= required_amount
    
    async def debit_credits(
        self,
        db: AsyncSession,
        user_id: int,
        amount: float,
        operation: OperationType,
        description: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Transaction:
        """
        Debita créditos da conta do usuário.
        
        Cria registro de transação e atualiza saldo.
        Usa lock pessimista para evitar race conditions.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            amount: Quantidade a debitar (valor positivo)
            operation: Tipo de operação
            description: Descrição da operação
            metadata: Dados adicionais em JSON
        
        Returns:
            Transaction: Registro da transação criada
        
        Raises:
            InsufficientCreditsError: Se saldo insuficiente
            UserNotFoundError: Se usuário não existe
        """
        # Buscar usuário com lock para atualização
        result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise UserNotFoundError(user_id)
        
        # Aplicar cobrança mínima
        charge_amount = max(amount, self.min_charge)
        
        # Verificar saldo
        if user.credits < charge_amount:
            raise InsufficientCreditsError(user.credits, charge_amount)
        
        # Atualizar saldo
        user.credits -= charge_amount
        new_balance = user.credits
        
        # Criar transação
        transaction = Transaction(
            user_id=user_id,
            operation=operation.value if isinstance(operation, OperationType) else operation,
            credits_used=-charge_amount,  # Negativo indica débito
            balance_after=new_balance,
            description=description,
            metadata_json=json.dumps(metadata) if metadata else None
        )
        db.add(transaction)
        
        logger.info(
            f"Créditos debitados: usuário={user_id}, "
            f"valor={charge_amount:.2f}, novo_saldo={new_balance:.2f}"
        )
        
        return transaction
    
    async def add_credits(
        self,
        db: AsyncSession,
        user_id: int,
        amount: float,
        operation: OperationType = OperationType.CREDIT_PURCHASE,
        description: Optional[str] = None
    ) -> Transaction:
        """
        Adiciona créditos à conta do usuário.
        
        Args:
            db: Sessão do banco de dados
            user_id: ID do usuário
            amount: Quantidade a adicionar
            operation: Tipo de operação (compra, bônus, etc.)
            description: Descrição da operação
        
        Returns:
            Transaction: Registro da transação criada
        """
        # Buscar usuário
        result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise UserNotFoundError(user_id)
        
        # Atualizar saldo
        user.credits += amount
        new_balance = user.credits
        
        # Criar transação
        transaction = Transaction(
            user_id=user_id,
            operation=operation.value if isinstance(operation, OperationType) else operation,
            credits_used=amount,  # Positivo indica crédito
            balance_after=new_balance,
            description=description
        )
        db.add(transaction)
        
        logger.info(
            f"Créditos adicionados: usuário={user_id}, "
            f"valor={amount:.2f}, novo_saldo={new_balance:.2f}"
        )
        
        return transaction
    
    def estimate_cost(
        self,
        duration_seconds: float,
        operation: OperationType = OperationType.VOICE_CLONE
    ) -> float:
        """
        Estima custo de uma operação.
        
        Args:
            duration_seconds: Duração do áudio em segundos
            operation: Tipo de operação
        
        Returns:
            float: Custo estimado em créditos
        """
        # Multiplicadores por tipo de operação
        multipliers = {
            OperationType.VOICE_CLONE: 1.0,
            OperationType.VOICE_CONVERT: 0.8,  # Conversão é mais rápida
            OperationType.PROFILE_CREATE: 0.0,  # Custo fixo
        }
        
        multiplier = multipliers.get(operation, 1.0)
        cost = duration_seconds * self.credits_per_second * multiplier
        
        # Aplicar mínimo
        return max(cost, self.min_charge)
    
    def estimate_duration(self, credits: float) -> float:
        """
        Estima duração de áudio que pode ser processado com os créditos.
        
        Args:
            credits: Quantidade de créditos disponíveis
        
        Returns:
            float: Duração estimada em segundos
        """
        return credits / self.credits_per_second
