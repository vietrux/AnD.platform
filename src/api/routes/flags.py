"""Flags API routes with full CRUD operations."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_db
from src.core.exceptions import (
    GameNotFoundError,
    FlagNotFoundError,
    TickNotFoundError,
)
from src.schemas import (
    FlagResponse,
    FlagListResponse,
    FlagUpdate,
    DeleteResponse,
)
from src.services import game_service, flag_service, tick_service


router = APIRouter(prefix="/flags", tags=["flags"])


class FlagStats(BaseModel):
    """Flag statistics response."""
    total_flags: int
    stolen_flags: int
    not_stolen_flags: int
    total_steals: int


# ============================================================================
# Flag CRUD Operations
# ============================================================================

@router.get("", response_model=FlagListResponse)
async def list_flags(
    game_id: uuid.UUID = Query(..., description="Game ID"),
    team_id: str | None = Query(None, description="Filter by team ID"),
    tick_id: uuid.UUID | None = Query(None, description="Filter by tick ID"),
    is_stolen: bool | None = Query(None, description="Filter by stolen status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    List all flags for a game with filtering.
    """
    game = await game_service.get_game(db, game_id)
    if not game:
        raise GameNotFoundError().to_http_exception()
    
    if tick_id:
        flags = await flag_service.list_tick_flags(db, tick_id)
    elif team_id:
        flags = await flag_service.list_team_flags(db, game_id, team_id, skip, limit)
    else:
        flags = await flag_service.list_flags(db, game_id, skip, limit)
    
    total = await flag_service.count_flags(db, game_id, is_stolen)
    
    return FlagListResponse.create(
        items=[FlagResponse.model_validate(f) for f in flags],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/stats", response_model=FlagStats)
async def get_flag_stats(
    game_id: uuid.UUID = Query(..., description="Game ID"),
    team_id: str | None = Query(None, description="Filter by team ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get flag statistics for a game or team.
    """
    game = await game_service.get_game(db, game_id)
    if not game:
        raise GameNotFoundError().to_http_exception()
    
    stats = await flag_service.get_flag_stats(db, game_id, team_id)
    return FlagStats(**stats)


@router.get("/by-value/{flag_value:path}", response_model=FlagResponse)
async def get_flag_by_value(
    flag_value: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a flag by its value.
    """
    flag = await flag_service.get_flag_by_value(db, flag_value)
    if not flag:
        raise FlagNotFoundError().to_http_exception()
    
    return flag


@router.get("/{flag_id}", response_model=FlagResponse)
async def get_flag(
    flag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific flag by ID.
    """
    flag = await flag_service.get_flag(db, flag_id)
    if not flag:
        raise FlagNotFoundError().to_http_exception()
    
    return flag


@router.patch("/{flag_id}", response_model=FlagResponse)
async def update_flag(
    flag_id: uuid.UUID,
    data: FlagUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a flag's properties.
    
    Note: Flag value cannot be changed after creation.
    """
    flag = await flag_service.get_flag(db, flag_id)
    if not flag:
        raise FlagNotFoundError().to_http_exception()
    
    return await flag_service.update_flag(db, flag, data)


@router.delete("/{flag_id}", response_model=DeleteResponse)
async def delete_flag(
    flag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a flag.
    
    Note: This will also affect related submissions.
    """
    flag = await flag_service.get_flag(db, flag_id)
    if not flag:
        raise FlagNotFoundError().to_http_exception()
    
    await flag_service.delete_flag(db, flag_id)
    return DeleteResponse(deleted_id=flag_id)


# ============================================================================
# Tick-based Flag Operations
# ============================================================================

@router.get("/tick/{tick_id}", response_model=FlagListResponse)
async def get_tick_flags(
    tick_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all flags for a specific tick.
    """
    tick = await tick_service.get_tick(db, tick_id)
    if not tick:
        raise TickNotFoundError().to_http_exception()
    
    flags = await flag_service.list_tick_flags(db, tick_id)
    
    return FlagListResponse.create(
        items=[FlagResponse.model_validate(f) for f in flags],
        total=len(flags),
        skip=skip,
        limit=limit,
    )


@router.get("/team/{team_id}/tick/{tick_id}", response_model=list[FlagResponse])
async def get_team_tick_flags(
    team_id: str,
    tick_id: uuid.UUID,
    game_id: uuid.UUID = Query(..., description="Game ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get flags for a specific team in a specific tick.
    """
    game = await game_service.get_game(db, game_id)
    if not game:
        raise GameNotFoundError().to_http_exception()
    
    tick = await tick_service.get_tick(db, tick_id)
    if not tick:
        raise TickNotFoundError().to_http_exception()
    
    flags = await flag_service.get_team_flags_for_tick(db, game_id, team_id, tick_id)
    return [FlagResponse.model_validate(f) for f in flags]


@router.post("/{flag_id}/mark-stolen", response_model=FlagResponse)
async def mark_flag_stolen(
    flag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually mark a flag as stolen.
    
    This is primarily for administrative purposes.
    """
    flag = await flag_service.get_flag(db, flag_id)
    if not flag:
        raise FlagNotFoundError().to_http_exception()
    
    return await flag_service.mark_flag_stolen(db, flag)
