from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator
from src.core.database import async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
