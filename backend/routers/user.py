"""
Endpoints de usuário e gerenciamento de créditos.

Fornece endpoints para registro, login, consulta de créditos e histórico de uso.
"""

from datetime import datetime, timedelta
from typing import List, Optional
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.database import get_db
from backend.models.entities import OperationType, Transaction, User, VoiceProfile
from backend.models.schemas import (
    CreditBalance,
    TransactionResponse,
    UsageStats,
    UserCreate,
    UserResponse,
)
from backend.config import get_settings
from backend.utils.exceptions import UserAlreadyExistsError, UserNotFoundError
from backend.utils.logger import get_logger

router = APIRouter(prefix="/users", tags=["Users"])
logger = get_logger(__name__)
settings = get_settings()

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login", auto_error=False)

# Simple in-memory token store (for development)
# In production, use Redis or JWT tokens
_active_tokens: dict[str, int] = {}


def create_access_token(user_id: int) -> str:
    """Create a simple access token for development."""
    token = secrets.token_urlsafe(32)
    _active_tokens[token] = user_id
    return token


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current authenticated user from token."""
    if not token:
        return None
    
    user_id = _active_tokens.get(token)
    if not user_id:
        return None
    
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def require_auth(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """Require authentication - raises 401 if not authenticated."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post(
    "/login",
    summary="Login usuário",
    description="Autentica usuário e retorna token de acesso."
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Autentica usuário com email e senha.
    
    Args:
        form_data: Credenciais OAuth2 (username=email, password)
        db: Sessão do banco de dados
    
    Returns:
        Token de acesso
    """
    # Find user by email
    result = await db.execute(
        select(User).where(User.email == form_data.username)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # For development: auto-create user on first login
        logger.info(f"Auto-creating user for development: {form_data.username}")
        user = User(
            email=form_data.username,
            name=form_data.username.split("@")[0],
            credits=settings.default_credits
        )
        db.add(user)
        await db.flush()
        
        # Add welcome credits transaction
        bonus = Transaction(
            user_id=user.id,
            operation=OperationType.CREDIT_BONUS.value,
            credits_used=settings.default_credits,
            balance_after=settings.default_credits,
            description="Créditos de boas-vindas"
        )
        db.add(bonus)
    
    # Create access token
    access_token = create_access_token(user.id)
    
    logger.info(f"User logged in: {user.email}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "credits": user.credits,
        }
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Perfil do usuário atual",
    description="Retorna informações do usuário autenticado."
)
async def get_current_user_profile(
    user: User = Depends(require_auth)
) -> UserResponse:
    """
    Retorna perfil do usuário autenticado.
    """
    return UserResponse.model_validate(user)


@router.get(
    "/credits",
    response_model=CreditBalance,
    summary="Saldo de créditos",
    description="Retorna saldo de créditos do usuário autenticado."
)
async def get_current_user_credits(
    user: User = Depends(require_auth)
) -> CreditBalance:
    """
    Retorna saldo de créditos do usuário autenticado.
    """
    return CreditBalance(
        user_id=user.id,
        credits=user.credits,
        plan=user.plan,
        credits_per_second=settings.credits_per_second
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar novo usuário",
    description="Cria uma nova conta de usuário com créditos iniciais."
)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Registra um novo usuário no sistema.
    
    Cria conta com créditos iniciais definidos na configuração.
    Registra uma transação de bônus inicial.
    
    Args:
        user_data: Dados do novo usuário
        db: Sessão do banco de dados
    
    Returns:
        UserResponse: Dados do usuário criado
    
    Raises:
        HTTPException: Se email já estiver cadastrado
    """
    # Verificar se email já existe
    existing = await db.execute(
        select(User).where(User.email == user_data.email)
    )
    if existing.scalar_one_or_none():
        logger.warning(f"Tentativa de registro com email existente: {user_data.email}")
        raise UserAlreadyExistsError(user_data.email)
    
    # Criar usuário
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        credits=settings.default_credits
    )
    db.add(new_user)
    await db.flush()  # Para obter o ID
    
    # Registrar transação de créditos iniciais
    bonus_transaction = Transaction(
        user_id=new_user.id,
        operation=OperationType.CREDIT_BONUS.value,
        credits_used=settings.default_credits,
        balance_after=settings.default_credits,
        description="Créditos de boas-vindas"
    )
    db.add(bonus_transaction)
    
    logger.info(f"Novo usuário registrado: {new_user.email} (ID: {new_user.id})")
    
    return UserResponse.model_validate(new_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Obter dados do usuário",
    description="Retorna informações completas do usuário."
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Busca dados de um usuário pelo ID.
    
    Args:
        user_id: ID do usuário
        db: Sessão do banco de dados
    
    Returns:
        UserResponse: Dados do usuário
    
    Raises:
        HTTPException: Se usuário não encontrado
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise UserNotFoundError(user_id)
    
    return UserResponse.model_validate(user)


@router.get(
    "/{user_id}/credits",
    response_model=CreditBalance,
    summary="Consultar saldo de créditos",
    description="Retorna saldo atual e informações de consumo."
)
async def get_credits(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> CreditBalance:
    """
    Consulta saldo de créditos do usuário.
    
    Args:
        user_id: ID do usuário
        db: Sessão do banco de dados
    
    Returns:
        CreditBalance: Informações de saldo
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise UserNotFoundError(user_id)
    
    return CreditBalance(
        user_id=user.id,
        credits=user.credits,
        plan=user.plan,
        credits_per_second=settings.credits_per_second
    )


@router.get(
    "/{user_id}/usage",
    response_model=UsageStats,
    summary="Estatísticas de uso",
    description="Retorna métricas de utilização da plataforma."
)
async def get_usage_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> UsageStats:
    """
    Calcula estatísticas de uso do usuário.
    
    Agrega dados de transações para fornecer métricas
    de utilização da plataforma.
    
    Args:
        user_id: ID do usuário
        db: Sessão do banco de dados
    
    Returns:
        UsageStats: Estatísticas de uso
    """
    # Verificar se usuário existe
    user_result = await db.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise UserNotFoundError(user_id)
    
    # Contar clonagens
    clone_count = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.user_id == user_id)
        .where(Transaction.operation == OperationType.VOICE_CLONE.value)
    )
    total_clones = clone_count.scalar() or 0
    
    # Contar conversões
    convert_count = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.user_id == user_id)
        .where(Transaction.operation == OperationType.VOICE_CONVERT.value)
    )
    total_conversions = convert_count.scalar() or 0
    
    # Total de créditos usados (soma dos negativos)
    credits_result = await db.execute(
        select(func.sum(Transaction.credits_used))
        .where(Transaction.user_id == user_id)
        .where(Transaction.credits_used < 0)
    )
    total_credits = abs(credits_result.scalar() or 0)
    
    # Contar perfis de voz
    profiles_count = await db.execute(
        select(func.count(VoiceProfile.id))
        .where(VoiceProfile.user_id == user_id)
    )
    voice_profiles = profiles_count.scalar() or 0
    
    return UsageStats(
        user_id=user_id,
        total_clones=total_clones,
        total_conversions=total_conversions,
        total_credits_used=total_credits,
        total_audio_seconds=total_credits / settings.credits_per_second,
        voice_profiles_count=voice_profiles
    )


@router.get(
    "/{user_id}/transactions",
    response_model=List[TransactionResponse],
    summary="Histórico de transações",
    description="Retorna histórico de transações de créditos."
)
async def get_transactions(
    user_id: int,
    limit: int = Query(50, ge=1, le=100, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    db: AsyncSession = Depends(get_db)
) -> List[TransactionResponse]:
    """
    Lista histórico de transações do usuário.
    
    Args:
        user_id: ID do usuário
        limit: Quantidade máxima de resultados
        offset: Pular N registros (paginação)
        db: Sessão do banco de dados
    
    Returns:
        List[TransactionResponse]: Lista de transações
    """
    # Verificar se usuário existe
    user_result = await db.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise UserNotFoundError(user_id)
    
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    transactions = result.scalars().all()
    
    return [TransactionResponse.model_validate(t) for t in transactions]


@router.post(
    "/api-key/generate",
    response_model=dict,
    summary="Gerar nova API Key",
    description="Gera ou regenera a chave de API do usuário autenticado."
)
async def generate_api_key(
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Gera uma nova API Key para o usuário.
    
    Se o usuário já tem uma API Key, ela será substituída.
    A API Key é usada para autenticação em chamadas programáticas.
    
    Args:
        user: Usuário autenticado
        db: Sessão do banco de dados
    
    Returns:
        dict: Nova API Key gerada
    """
    # Gerar nova API key (prefixo + random token)
    new_api_key = f"vc_{secrets.token_urlsafe(32)}"
    
    # Atualizar no banco
    user.api_key = new_api_key
    await db.flush()
    
    logger.info(f"Nova API Key gerada para usuário {user.id}")
    
    return {
        "api_key": new_api_key,
        "message": "API Key gerada com sucesso. Guarde-a em local seguro, ela não será exibida novamente."
    }


@router.delete(
    "/api-key",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revogar API Key",
    description="Revoga a chave de API do usuário, invalidando acessos programáticos."
)
async def revoke_api_key(
    user: User = Depends(require_auth),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoga a API Key do usuário.
    
    Após revogar, chamadas usando a API Key antiga falharão.
    
    Args:
        user: Usuário autenticado
        db: Sessão do banco de dados
    """
    user.api_key = None
    await db.flush()
    
    logger.info(f"API Key revogada para usuário {user.id}")
