"""
Configuração do banco de dados SQLite com SQLAlchemy async.

Fornece engine, session maker e base declarativa para os modelos ORM.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.config import get_settings

settings = get_settings()

# Engine assíncrona para SQLite
# echo=True em debug para ver as queries SQL geradas
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# Session maker assíncrono
# expire_on_commit=False evita problemas ao acessar atributos após commit
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """
    Base declarativa para todos os modelos ORM.
    
    Todos os modelos devem herdar desta classe para serem
    reconhecidos pelo SQLAlchemy e incluídos nas migrations.
    """
    pass


async def init_db() -> None:
    """
    Inicializa o banco de dados.
    
    Cria todas as tabelas definidas nos modelos que herdam de Base.
    Em produção, considere usar Alembic para migrations.
    """
    # Importar entidades para registrar os modelos
    from backend.models import entities  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection para obter sessão do banco.
    
    Yields:
        AsyncSession: Sessão assíncrona do SQLAlchemy
    
    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
