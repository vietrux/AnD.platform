"""Tick service with full CRUD operations."""

import uuid
from datetime import datetime
from typing import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Tick, TickStatus
from src.services.base import BaseService
from src.schemas import TickCreate, TickUpdate


class TickService(BaseService[Tick, TickCreate, TickUpdate]):
    """Service for Tick CRUD operations."""
    
    def __init__(self):
        super().__init__(Tick)
    
    async def get_by_game(
        self,
        db: AsyncSession,
        game_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Tick]:
        """Get ticks by game."""
        result = await db.execute(
            select(Tick)
            .where(Tick.game_id == game_id)
            .order_by(Tick.tick_number.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_by_number(
        self,
        db: AsyncSession,
        game_id: uuid.UUID,
        tick_number: int,
    ) -> Tick | None:
        """Get tick by game and tick number."""
        result = await db.execute(
            select(Tick).where(
                Tick.game_id == game_id,
                Tick.tick_number == tick_number,
            )
        )
        return result.scalar_one_or_none()
    
    async def get_current(
        self,
        db: AsyncSession,
        game_id: uuid.UUID,
    ) -> Tick | None:
        """Get current active tick."""
        result = await db.execute(
            select(Tick)
            .where(
                Tick.game_id == game_id,
                Tick.status == TickStatus.ACTIVE,
            )
            .order_by(Tick.tick_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_latest(
        self,
        db: AsyncSession,
        game_id: uuid.UUID,
    ) -> Tick | None:
        """Get the latest tick."""
        result = await db.execute(
            select(Tick)
            .where(Tick.game_id == game_id)
            .order_by(Tick.tick_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def count_by_game(
        self,
        db: AsyncSession,
        game_id: uuid.UUID,
        status: TickStatus | None = None,
    ) -> int:
        """Count ticks for a game."""
        query = select(func.count()).select_from(Tick).where(Tick.game_id == game_id)
        if status:
            query = query.where(Tick.status == status)
        result = await db.execute(query)
        return result.scalar() or 0
    
    async def create_tick(
        self,
        db: AsyncSession,
        game_id: uuid.UUID,
        tick_number: int,
    ) -> Tick:
        """Create a new tick."""
        tick = Tick(
            game_id=game_id,
            tick_number=tick_number,
            status=TickStatus.PENDING,
        )
        db.add(tick)
        await db.commit()
        await db.refresh(tick)
        return tick
    
    async def start_tick(
        self,
        db: AsyncSession,
        tick: Tick,
    ) -> Tick:
        """Start a tick."""
        tick.status = TickStatus.ACTIVE
        tick.start_time = datetime.utcnow()
        await db.commit()
        await db.refresh(tick)
        return tick
    
    async def complete_tick(
        self,
        db: AsyncSession,
        tick: Tick,
        flags_placed: int = 0,
    ) -> Tick:
        """Complete a tick."""
        tick.status = TickStatus.COMPLETED
        tick.end_time = datetime.utcnow()
        tick.flags_placed = flags_placed
        await db.commit()
        await db.refresh(tick)
        return tick
    
    async def error_tick(
        self,
        db: AsyncSession,
        tick: Tick,
    ) -> Tick:
        """Mark tick as errored."""
        tick.status = TickStatus.ERROR
        tick.end_time = datetime.utcnow()
        await db.commit()
        await db.refresh(tick)
        return tick


# Module-level service instance
_tick_service = TickService()


# Function exports
async def get_tick(db: AsyncSession, tick_id: uuid.UUID) -> Tick | None:
    """Get tick by ID."""
    return await _tick_service.get(db, tick_id)


async def list_ticks(
    db: AsyncSession,
    game_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[Tick]:
    """List ticks for a game."""
    return await _tick_service.get_by_game(db, game_id, skip, limit)


async def get_tick_by_number(
    db: AsyncSession,
    game_id: uuid.UUID,
    tick_number: int,
) -> Tick | None:
    """Get tick by number."""
    return await _tick_service.get_by_number(db, game_id, tick_number)


async def get_current_tick(
    db: AsyncSession,
    game_id: uuid.UUID,
) -> Tick | None:
    """Get current active tick."""
    return await _tick_service.get_current(db, game_id)


async def get_latest_tick(
    db: AsyncSession,
    game_id: uuid.UUID,
) -> Tick | None:
    """Get latest tick."""
    return await _tick_service.get_latest(db, game_id)


async def count_ticks(
    db: AsyncSession,
    game_id: uuid.UUID,
    status: TickStatus | None = None,
) -> int:
    """Count ticks for a game."""
    return await _tick_service.count_by_game(db, game_id, status)


async def create_tick(
    db: AsyncSession,
    game_id: uuid.UUID,
    tick_number: int,
) -> Tick:
    """Create a new tick."""
    return await _tick_service.create_tick(db, game_id, tick_number)


async def update_tick(
    db: AsyncSession,
    tick: Tick,
    data: TickUpdate,
) -> Tick:
    """Update tick."""
    return await _tick_service.update(db, db_obj=tick, obj_in=data)


async def delete_tick(db: AsyncSession, tick_id: uuid.UUID) -> Tick | None:
    """Delete a tick."""
    return await _tick_service.delete(db, id=tick_id)


async def start_tick(db: AsyncSession, tick: Tick) -> Tick:
    """Start a tick."""
    return await _tick_service.start_tick(db, tick)


async def complete_tick(
    db: AsyncSession,
    tick: Tick,
    flags_placed: int = 0,
) -> Tick:
    """Complete a tick."""
    return await _tick_service.complete_tick(db, tick, flags_placed)
