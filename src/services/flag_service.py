import uuid
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.models import Flag, FlagType, Tick


def generate_flag_value(
    game_id: uuid.UUID,
    team_id: str,
    tick_number: int,
    flag_type: FlagType,
) -> str:
    settings = get_settings()
    random_part = secrets.token_hex(8)
    
    data = f"{game_id}:{team_id}:{tick_number}:{flag_type.value}:{random_part}"
    signature = hmac.new(
        settings.flag_secret_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()[:16]
    
    return f"FLAG{{{signature}_{random_part}}}"


async def create_flag(
    db: AsyncSession,
    game_id: uuid.UUID,
    team_id: str,
    tick: Tick,
    flag_type: FlagType,
) -> Flag:
    # Check if flag already exists for this game/team/tick/type
    existing = await db.execute(
        select(Flag).where(
            Flag.game_id == game_id,
            Flag.team_id == team_id,
            Flag.tick_id == tick.id,
            Flag.flag_type == flag_type,
        )
    )
    existing_flag = existing.scalar_one_or_none()
    if existing_flag:
        return existing_flag
    
    settings = get_settings()
    
    flag_value = generate_flag_value(game_id, team_id, tick.tick_number, flag_type)
    validity_seconds = settings.tick_duration_seconds * settings.flag_validity_ticks
    valid_until = datetime.utcnow() + timedelta(seconds=validity_seconds)
    
    flag = Flag(
        game_id=game_id,
        team_id=team_id,
        tick_id=tick.id,
        flag_type=flag_type,
        flag_value=flag_value,
        valid_until=valid_until,
    )
    db.add(flag)
    await db.commit()
    await db.refresh(flag)
    return flag


async def get_flag(db: AsyncSession, flag_id: uuid.UUID) -> Flag | None:
    result = await db.execute(select(Flag).where(Flag.id == flag_id))
    return result.scalar_one_or_none()


async def get_flag_by_value(db: AsyncSession, flag_value: str) -> Flag | None:
    result = await db.execute(select(Flag).where(Flag.flag_value == flag_value))
    return result.scalar_one_or_none()


async def mark_flag_stolen(db: AsyncSession, flag: Flag) -> Flag:
    flag.is_stolen = True
    flag.stolen_count += 1
    await db.commit()
    await db.refresh(flag)
    return flag


async def get_team_flags_for_tick(
    db: AsyncSession,
    game_id: uuid.UUID,
    team_id: str,
    tick_id: uuid.UUID,
) -> list[Flag]:
    result = await db.execute(
        select(Flag).where(
            Flag.game_id == game_id,
            Flag.team_id == team_id,
            Flag.tick_id == tick_id,
        )
    )
    return list(result.scalars().all())


async def list_flags(
    db: AsyncSession,
    game_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> list[Flag]:
    result = await db.execute(
        select(Flag)
        .where(Flag.game_id == game_id)
        .order_by(Flag.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_team_flags(
    db: AsyncSession,
    game_id: uuid.UUID,
    team_id: str,
    skip: int = 0,
    limit: int = 50,
) -> list[Flag]:
    result = await db.execute(
        select(Flag)
        .where(Flag.game_id == game_id, Flag.team_id == team_id)
        .order_by(Flag.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def list_tick_flags(
    db: AsyncSession,
    tick_id: uuid.UUID,
) -> list[Flag]:
    result = await db.execute(
        select(Flag)
        .where(Flag.tick_id == tick_id)
        .order_by(Flag.created_at.desc())
    )
    return list(result.scalars().all())


async def count_flags(
    db: AsyncSession,
    game_id: uuid.UUID,
    is_stolen: bool | None = None,
) -> int:
    query = select(func.count()).select_from(Flag).where(Flag.game_id == game_id)
    if is_stolen is not None:
        query = query.where(Flag.is_stolen == is_stolen)
    result = await db.execute(query)
    return result.scalar() or 0


async def get_flag_stats(
    db: AsyncSession,
    game_id: uuid.UUID,
    team_id: str | None = None,
) -> dict:
    from src.models import FlagSubmission, SubmissionStatus
    
    # Total flags
    total_query = select(func.count()).select_from(Flag).where(Flag.game_id == game_id)
    if team_id:
        total_query = total_query.where(Flag.team_id == team_id)
    total_result = await db.execute(total_query)
    total_flags = total_result.scalar() or 0
    
    # Stolen flags
    stolen_query = select(func.count()).select_from(Flag).where(
        Flag.game_id == game_id,
        Flag.is_stolen == True,
    )
    if team_id:
        stolen_query = stolen_query.where(Flag.team_id == team_id)
    stolen_result = await db.execute(stolen_query)
    stolen_flags = stolen_result.scalar() or 0
    
    # Total steals (sum of stolen_count)
    steals_query = select(func.sum(Flag.stolen_count)).where(Flag.game_id == game_id)
    if team_id:
        steals_query = steals_query.where(Flag.team_id == team_id)
    steals_result = await db.execute(steals_query)
    total_steals = steals_result.scalar() or 0
    
    # Attack stats: flags captured by this team (from submissions)
    flags_captured = 0
    flags_lost = 0
    
    if team_id:
        # Flags this team successfully captured
        captured_query = select(func.count()).select_from(FlagSubmission).where(
            FlagSubmission.game_id == game_id,
            FlagSubmission.attacker_team_id == team_id,
            FlagSubmission.status == SubmissionStatus.ACCEPTED,
        )
        captured_result = await db.execute(captured_query)
        flags_captured = captured_result.scalar() or 0
        
        # Defense stats: this team's flags that were stolen (already computed above)
        flags_lost = stolen_flags
    
    return {
        "total_flags": total_flags,
        "stolen_flags": stolen_flags,
        "not_stolen_flags": total_flags - stolen_flags,
        "total_steals": total_steals,
        "flags_captured": flags_captured,
        "flags_lost": flags_lost,
    }

