"""Ticks API routes - Read-only operations for admin/debug."""

import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_db
from src.core.exceptions import GameNotFoundError, TickNotFoundError
from src.models import TickStatus
from src.schemas import TickResponse, TickListResponse
from src.services import game_service, tick_service


router = APIRouter(prefix="/ticks", tags=["ticks"])


@router.get("", response_model=TickListResponse)
async def list_ticks(
    game_id: uuid.UUID = Query(..., description="Game ID"),
    status: str | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise GameNotFoundError().to_http_exception()
    
    ticks = await tick_service.list_ticks(db, game_id, skip, limit)
    
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
    tick = await tick_service.get_tick(db, tick_id)
    if not tick:
        raise TickNotFoundError().to_http_exception()
    
    return tick
