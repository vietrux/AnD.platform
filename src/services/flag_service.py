import uuid
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta
from sqlalchemy import select
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
