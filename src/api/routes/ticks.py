"""Ticks API routes with full CRUD operations."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_db
from src.core.exceptions import (
    GameNotFoundError,
    TickNotFoundError,
)
from src.models import TickStatus
from src.schemas import (
    TickResponse,
    TickListResponse,
    TickUpdate,
    MessageResponse,
    DeleteResponse,
)
from src.services import game_service
from src.services import tick_service


router = APIRouter(prefix="/ticks", tags=["ticks"])


# ============================================================================
# Tick CRUD Operations
# ============================================================================

@router.get("", response_model=TickListResponse)
async def list_ticks(
    game_id: uuid.UUID = Query(..., description="Game ID"),
    status: str | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    List all ticks for a game with pagination.
    """
    game = await game_service.get_game(db, game_id)
    if not game:
        raise GameNotFoundError().to_http_exception()
    
    ticks = await tick_service.list_ticks(db, game_id, skip, limit)
    
    # Convert status enum if filtering
    status_filter = TickStatus(status) if status else None
    total = await tick_service.count_ticks(db, game_id, status_filter)
    
    return TickListResponse.create(
        items=[TickResponse.model_validate(t) for t in ticks],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/current", response_model=TickResponse | None)
async def get_current_tick(
    game_id: uuid.UUID = Query(..., description="Game ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the currently active tick for a game.
    """
    game = await game_service.get_game(db, game_id)
    if not game:
        raise GameNotFoundError().to_http_exception()
    
    tick = await tick_service.get_current_tick(db, game_id)
    if not tick:
        return None
    
    return tick


@router.get("/latest", response_model=TickResponse | None)
async def get_latest_tick(
    game_id: uuid.UUID = Query(..., description="Game ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the most recent tick for a game.
    """
    game = await game_service.get_game(db, game_id)
    if not game:
        raise GameNotFoundError().to_http_exception()
    
    tick = await tick_service.get_latest_tick(db, game_id)
    if not tick:
        return None
    
    return tick


@router.get("/number/{tick_number}", response_model=TickResponse)
async def get_tick_by_number(
    tick_number: int,
    game_id: uuid.UUID = Query(..., description="Game ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific tick by its number.
    """
    game = await game_service.get_game(db, game_id)
    if not game:
        raise GameNotFoundError().to_http_exception()
    
    tick = await tick_service.get_tick_by_number(db, game_id, tick_number)
    if not tick:
        raise TickNotFoundError().to_http_exception()
    
    return tick


@router.get("/{tick_id}", response_model=TickResponse)
async def get_tick(
    tick_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific tick by ID.
    """
    tick = await tick_service.get_tick(db, tick_id)
    if not tick:
        raise TickNotFoundError().to_http_exception()
    
    return tick


@router.post("", response_model=TickResponse, status_code=201)
async def create_tick(
    game_id: uuid.UUID = Query(..., description="Game ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new tick for a game.
    
    The tick number is automatically determined based on existing ticks.
    """
    game = await game_service.get_game(db, game_id)
    if not game:
        raise GameNotFoundError().to_http_exception()
    
    # Determine next tick number
    latest_tick = await tick_service.get_latest_tick(db, game_id)
    tick_number = (latest_tick.tick_number + 1) if latest_tick else 1
    
    tick = await tick_service.create_tick(db, game_id, tick_number)
    return tick


@router.patch("/{tick_id}", response_model=TickResponse)
async def update_tick(
    tick_id: uuid.UUID,
    data: TickUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a tick's properties.
    """
    tick = await tick_service.get_tick(db, tick_id)
    if not tick:
        raise TickNotFoundError().to_http_exception()
    
    return await tick_service.update_tick(db, tick, data)


@router.delete("/{tick_id}", response_model=DeleteResponse)
async def delete_tick(
    tick_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a tick.
    
    Note: This will also delete associated flags and service statuses.
    """
    tick = await tick_service.get_tick(db, tick_id)
    if not tick:
        raise TickNotFoundError().to_http_exception()
    
    await tick_service.delete_tick(db, tick_id)
    return DeleteResponse(deleted_id=tick_id)


# ============================================================================
# Tick Lifecycle Operations
# ============================================================================

@router.post("/{tick_id}/start", response_model=TickResponse)
async def start_tick(
    tick_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Start a pending tick.
    """
    tick = await tick_service.get_tick(db, tick_id)
    if not tick:
        raise TickNotFoundError().to_http_exception()
    
    if tick.status != TickStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start tick in {tick.status} state"
        )
    
    return await tick_service.start_tick(db, tick)


@router.post("/{tick_id}/complete", response_model=TickResponse)
async def complete_tick(
    tick_id: uuid.UUID,
    flags_placed: int = Query(0, ge=0, description="Number of flags placed"),
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a tick as completed.
    """
    tick = await tick_service.get_tick(db, tick_id)
    if not tick:
        raise TickNotFoundError().to_http_exception()
    
    if tick.status != TickStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete tick in {tick.status} state"
        )
    
    return await tick_service.complete_tick(db, tick, flags_placed)
