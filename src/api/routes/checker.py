import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_db, ServiceStatusNotFoundError, GameNotFoundError
from src.schemas import DeleteResponse
from src.schemas.service_status import ServiceStatusResponse, ServiceStatusListResponse
from src.services import game_service
from src.services import checker_service


router = APIRouter(prefix="/checker", tags=["checker"])


@router.get("/statuses", response_model=ServiceStatusListResponse)
async def list_checker_statuses(
    game_id: uuid.UUID | None = Query(None, description="Filter by game ID"),
    team_id: str | None = Query(None, description="Filter by team ID"),
    tick_id: uuid.UUID | None = Query(None, description="Filter by tick ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    if game_id:
        game = await game_service.get_game(db, game_id)
        if not game:
            raise GameNotFoundError().to_http_exception()
    
    statuses = await checker_service.list_service_statuses(
        db, game_id, team_id, tick_id, skip, limit
    )
    total = await checker_service.count_service_statuses(db, game_id, team_id)
    
    return ServiceStatusListResponse.create(
        items=[ServiceStatusResponse.model_validate(s) for s in statuses],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/statuses/{status_id}", response_model=ServiceStatusResponse)
async def get_checker_status(
    status_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    status = await checker_service.get_service_status(db, status_id)
    if not status:
        raise ServiceStatusNotFoundError().to_http_exception()
    
    return status


@router.delete("/statuses/{status_id}", response_model=DeleteResponse)
async def delete_checker_status(
    status_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    status = await checker_service.get_service_status(db, status_id)
    if not status:
        raise ServiceStatusNotFoundError().to_http_exception()
    
    await checker_service.delete_service_status(db, status_id)
    return DeleteResponse(deleted_id=status_id)

