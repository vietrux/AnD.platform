import uuid
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ServiceStatus, Scoreboard, CheckStatus


SLA_POINTS_PER_TICK = 100


async def record_service_status(
    db: AsyncSession,
    game_id: uuid.UUID,
    team_id: str,
    tick_id: uuid.UUID,
    status: CheckStatus,
    sla_percentage: float,
    error_message: str | None = None,
    check_duration_ms: int | None = None,
) -> ServiceStatus:
    # Check if service status already exists for this game/team/tick
    result = await db.execute(
        select(ServiceStatus).where(
            ServiceStatus.game_id == game_id,
            ServiceStatus.team_id == team_id,
            ServiceStatus.tick_id == tick_id,
        )
    )
    existing_status = result.scalar_one_or_none()
    
    if existing_status:
        # Already recorded for this tick, skip
        return existing_status
    
    service_status = ServiceStatus(
        game_id=game_id,
        team_id=team_id,
        tick_id=tick_id,
        status=status,
        sla_percentage=sla_percentage,
        error_message=error_message,
        check_duration_ms=check_duration_ms,
    )
    db.add(service_status)
    
    sla_points = int((sla_percentage / 100.0) * SLA_POINTS_PER_TICK)
    await update_team_sla_score(db, game_id, team_id, sla_points)
    
    await db.commit()
    await db.refresh(service_status)
    return service_status


async def update_team_sla_score(
    db: AsyncSession,
    game_id: uuid.UUID,
    team_id: str,
    sla_points: int,
) -> None:
    result = await db.execute(
        select(Scoreboard).where(
            Scoreboard.game_id == game_id,
            Scoreboard.team_id == team_id,
        )
    )
    scoreboard = result.scalar_one_or_none()
    
    if scoreboard:
        scoreboard.sla_points += sla_points
        scoreboard.total_points = (
            scoreboard.attack_points + 
            scoreboard.defense_points + 
            scoreboard.sla_points
        )
        scoreboard.last_updated = datetime.utcnow()


async def update_rankings(db: AsyncSession, game_id: uuid.UUID) -> None:
    result = await db.execute(
        select(Scoreboard)
        .where(Scoreboard.game_id == game_id)
        .order_by(Scoreboard.total_points.desc())
    )
    scoreboards = list(result.scalars().all())
    
    for rank, scoreboard in enumerate(scoreboards, 1):
        scoreboard.rank = rank
    
    await db.commit()


async def get_scoreboard(db: AsyncSession, game_id: uuid.UUID) -> list[Scoreboard]:
    result = await db.execute(
        select(Scoreboard)
        .where(Scoreboard.game_id == game_id)
        .order_by(Scoreboard.rank.asc())
    )
    return list(result.scalars().all())
