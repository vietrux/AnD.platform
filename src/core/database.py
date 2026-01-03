import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from src.core.config import get_settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

db_initialized = asyncio.Event()


async def init_db(max_retries: int = 30, retry_delay: float = 1.0) -> None:
    for attempt in range(max_retries):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                await conn.run_sync(_apply_schema_migrations)
            logger.info("Database initialized successfully")
            db_initialized.set()
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                raise


def _apply_schema_migrations(connection) -> None:
    from sqlalchemy import text, inspect
    
    inspector = inspect(connection)
    
    if "games" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("games")]
        if "max_ticks" not in columns:
            connection.execute(text("ALTER TABLE games ADD COLUMN max_ticks INTEGER DEFAULT NULL"))
            logger.info("Added max_ticks column to games table")


async def wait_for_db(timeout: float = 60.0) -> bool:
    try:
        await asyncio.wait_for(db_initialized.wait(), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        return False


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
