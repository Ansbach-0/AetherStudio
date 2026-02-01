"""
Configuração do banco de dados SQLite com SQLAlchemy async.

Fornece engine, session maker e base declarativa para os modelos ORM.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.config import get_settings
from backend.utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)

# Engine assíncrona para SQLite
# echo=False para não poluir logs com queries SQL
engine = create_async_engine(
    settings.database_url,
    echo=False,
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
        await ensure_users_api_key_column(conn)
        await ensure_voice_profiles_columns(conn)

    logger.info("Banco de dados pronto", database_url=settings.database_url)


async def ensure_users_api_key_column(conn) -> None:
    if "sqlite" not in settings.database_url:
        return

    result = await conn.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    )
    if result.first() is None:
        return

    result = await conn.exec_driver_sql("PRAGMA table_info(users)")
    columns = {row[1] for row in result.fetchall()}
    if "api_key" in columns:
        return

    await conn.exec_driver_sql("ALTER TABLE users ADD COLUMN api_key VARCHAR")
    logger.info("Coluna users.api_key adicionada")


async def ensure_voice_profiles_columns(conn) -> None:
    if "sqlite" not in settings.database_url:
        return

    result = await conn.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='voice_profiles'"
    )
    if result.first() is None:
        return

    result = await conn.exec_driver_sql("PRAGMA table_info(voice_profiles)")
    columns = {row[1] for row in result.fetchall()}
    
    if "reference_text" not in columns:
        await conn.exec_driver_sql("ALTER TABLE voice_profiles ADD COLUMN reference_text TEXT")
        logger.info("Coluna voice_profiles.reference_text adicionada")
    
    if "color" not in columns:
        await conn.exec_driver_sql("ALTER TABLE voice_profiles ADD COLUMN color VARCHAR(7)")
        logger.info("Coluna voice_profiles.color adicionada")
    
    if "tags" not in columns:
        await conn.exec_driver_sql("ALTER TABLE voice_profiles ADD COLUMN tags VARCHAR(200)")
        logger.info("Coluna voice_profiles.tags adicionada")
    
    if "updated_at" not in columns:
        await conn.exec_driver_sql(
            "ALTER TABLE voice_profiles ADD COLUMN updated_at DATETIME"
        )
        logger.info("Coluna voice_profiles.updated_at adicionada")


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
