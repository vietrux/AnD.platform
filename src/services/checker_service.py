import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ServiceStatus, CheckStatus


async def list_service_statuses(
    db: AsyncSession,
    game_id: uuid.UUID | None = None,
    team_id: str | None = None,
    tick_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[ServiceStatus]:
    query = select(ServiceStatus)
    
    if game_id:
        query = query.where(ServiceStatus.game_id == game_id)
    if team_id:
        query = query.where(ServiceStatus.team_id == team_id)
    if tick_id:
        query = query.where(ServiceStatus.tick_id == tick_id)
    
    query = query.order_by(ServiceStatus.checked_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_service_status(
    db: AsyncSession, status_id: uuid.UUID
) -> ServiceStatus | None:
    result = await db.execute(
        select(ServiceStatus).where(ServiceStatus.id == status_id)
    )
    return result.scalar_one_or_none()


async def count_service_statuses(
    db: AsyncSession,
    game_id: uuid.UUID | None = None,
    team_id: str | None = None,
    status: CheckStatus | None = None,
) -> int:
    query = select(func.count(ServiceStatus.id))
    
    if game_id:
        query = query.where(ServiceStatus.game_id == game_id)
    if team_id:
        query = query.where(ServiceStatus.team_id == team_id)
    if status:
        query = query.where(ServiceStatus.status == status)
    
    result = await db.execute(query)
    return result.scalar() or 0


async def delete_service_status(
    db: AsyncSession, status_id: uuid.UUID
) -> bool:
    status = await get_service_status(db, status_id)
    if status:
        await db.delete(status)
        await db.commit()
        return True
    return False


async def list_team_service_statuses(
    db: AsyncSession,
    team_id: str,
    game_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[ServiceStatus]:
    query = select(ServiceStatus).where(ServiceStatus.team_id == team_id)
    
    if game_id:
        query = query.where(ServiceStatus.game_id == game_id)
    
    query = query.order_by(ServiceStatus.checked_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
