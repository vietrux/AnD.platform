import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_db
from src.schemas import ScoreboardResponse, ScoreboardEntry
from src.services import scoring_service, game_service


router = APIRouter(prefix="/scoreboard", tags=["scoreboard"])


@router.get("/{game_id}", response_model=ScoreboardResponse)
async def get_scoreboard(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    scoreboards = await scoring_service.get_scoreboard(db, game_id)
    
    entries = [
        ScoreboardEntry(
            team_id=s.team_id,
            attack_points=s.attack_points,
            defense_points=s.defense_points,
            sla_points=s.sla_points,
            total_points=s.total_points,
            rank=s.rank,
            flags_captured=s.flags_captured,
            flags_lost=s.flags_lost,
        )
        for s in scoreboards
    ]
    
    last_updated = max((s.last_updated for s in scoreboards), default=None)
    
    return ScoreboardResponse(
        game_id=game_id,
        game_name=game.name,
        current_tick=game.current_tick,
        entries=entries,
        last_updated=last_updated,
    )
