"""
Entidades ORM do banco de dados.

Define os modelos que representam as tabelas do banco de dados
usando SQLAlchemy 2.0 com tipagem moderna.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.models.database import Base


class PlanType(str, Enum):
    """Tipos de plano disponíveis para usuários."""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class OperationType(str, Enum):
    """Tipos de operação que consomem créditos."""
    VOICE_CLONE = "voice_clone"
    VOICE_CONVERT = "voice_convert"
    PROFILE_CREATE = "profile_create"
    CREDIT_PURCHASE = "credit_purchase"
    CREDIT_BONUS = "credit_bonus"


class User(Base):
    """
    Modelo de usuário do sistema.
    
    Armazena informações do usuário, saldo de créditos
    e plano de assinatura.
    
    Attributes:
        id: Identificador único do usuário
        email: Email único do usuário
        name: Nome de exibição
        credits: Saldo atual de créditos
        plan: Tipo de plano (free, basic, pro, enterprise)
        api_key: Chave de API para acesso programático
        is_active: Se o usuário está ativo
        created_at: Data de criação da conta
        updated_at: Data da última atualização
    """
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    credits: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    plan: Mapped[str] = mapped_column(String(20), default=PlanType.FREE.value, nullable=False)
    api_key: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relacionamentos
    voice_profiles: Mapped[List["VoiceProfile"]] = relationship(
        "VoiceProfile",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', plan='{self.plan}')>"


class VoiceProfile(Base):
    """
    Perfil de voz salvo pelo usuário.
    
    Armazena referência ao áudio de amostra e configurações
    para clonagem de voz.
    
    Attributes:
        id: Identificador único do perfil
        user_id: ID do usuário proprietário
        name: Nome do perfil de voz
        description: Descrição opcional do perfil
        reference_audio_path: Caminho para o áudio de referência
        reference_text: Transcrição do áudio de referência (para F5-TTS)
        language: Idioma do perfil (pt-BR, en-US, etc.)
        color: Cor hexadecimal para avatar/UI
        tags: Tags de estilo separadas por vírgula
        is_public: Se o perfil é público para outros usuários
        created_at: Data de criação do perfil
    """
    __tablename__ = "voice_profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_audio_path: Mapped[str] = mapped_column(String(500), nullable=False)
    reference_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="pt-BR", nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(7), default="#7c3aed", nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_public: Mapped[bool] = mapped_column(default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relacionamentos
    user: Mapped["User"] = relationship("User", back_populates="voice_profiles")
    
    def __repr__(self) -> str:
        return f"<VoiceProfile(id={self.id}, name='{self.name}', language='{self.language}')>"


class Transaction(Base):
    """
    Registro de transação de créditos.
    
    Mantém histórico de todas as operações que afetam
    o saldo de créditos do usuário.
    
    Attributes:
        id: Identificador único da transação
        user_id: ID do usuário
        operation: Tipo de operação realizada
        credits_used: Quantidade de créditos (positivo = adição, negativo = uso)
        balance_after: Saldo após a transação
        description: Descrição da operação
        metadata: Dados adicionais em JSON (ex: duração do áudio)
        created_at: Data da transação
    """
    __tablename__ = "transactions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    operation: Mapped[str] = mapped_column(String(50), nullable=False)
    credits_used: Mapped[float] = mapped_column(Float, nullable=False)
    balance_after: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relacionamentos
    user: Mapped["User"] = relationship("User", back_populates="transactions")
    
    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, operation='{self.operation}', credits={self.credits_used})>"
