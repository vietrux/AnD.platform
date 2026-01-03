import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_db, GameNotFoundError, TeamNotFoundError
from src.schemas import ScoreboardResponse, ScoreboardEntry
from src.services import scoring_service, game_service


router = APIRouter(prefix="/scoreboard", tags=["scoreboard"])


@router.get("", response_model=list[ScoreboardResponse])
async def list_scoreboards(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    games = await game_service.list_games(db, skip, limit)
    
    responses = []
    for game in games:
        scoreboards = await scoring_service.get_scoreboard(db, game.id)
        
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
        
        responses.append(ScoreboardResponse(
            game_id=game.id,
            game_name=game.name,
            current_tick=game.current_tick,
            entries=entries,
            last_updated=last_updated,
        ))
    
    return responses


@router.get("/{game_id}", response_model=ScoreboardResponse)
async def get_scoreboard(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise GameNotFoundError().to_http_exception()
    
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


@router.get("/{game_id}/team/{team_id}", response_model=ScoreboardEntry)
async def get_team_score(
    game_id: uuid.UUID,
    team_id: str,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise GameNotFoundError().to_http_exception()
    
    scoreboard = await scoring_service.get_team_scoreboard(db, game_id, team_id)
    if not scoreboard:
        raise TeamNotFoundError().to_http_exception()
    
    return ScoreboardEntry(
        team_id=scoreboard.team_id,
        attack_points=scoreboard.attack_points,
        defense_points=scoreboard.defense_points,
        sla_points=scoreboard.sla_points,
        total_points=scoreboard.total_points,
        rank=scoreboard.rank,
        flags_captured=scoreboard.flags_captured,
        flags_lost=scoreboard.flags_lost,
    )

