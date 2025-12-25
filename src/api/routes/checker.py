from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_db
from src.models import TickStatus
from src.schemas import CheckerStatusSubmit, CheckerStatusResponse
from src.services import scoring_service, game_service


router = APIRouter(prefix="/checker", tags=["checker"])


@router.post("/status", response_model=CheckerStatusResponse)
async def submit_checker_status(
    data: CheckerStatusSubmit,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, data.game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    await scoring_service.record_service_status(
        db=db,
        game_id=data.game_id,
        team_id=data.team_id,
        tick_id=data.tick_id,
        status=data.status,
        sla_percentage=data.sla_percentage,
        error_message=data.message,
        check_duration_ms=data.check_duration_ms,
    )
    
    return CheckerStatusResponse(
        success=True,
        message=f"Status recorded: {data.status.value}"
    )
