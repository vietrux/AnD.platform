import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_db, get_settings
from src.models import GameStatus
from src.schemas import (
    GameCreate,
    GameUpdate,
    GameTeamAdd,
    GameResponse,
    GameTeamResponse,
    GameListResponse,
)
from src.services import game_service, docker_service

router = APIRouter(prefix="/games", tags=["games"])


@router.post("", response_model=GameResponse)
async def create_game(
    data: GameCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await game_service.get_game_by_name(db, data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Game name already exists")
    
    game = await game_service.create_game(db, data)
    return game


@router.get("", response_model=GameListResponse)
async def list_games(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    games = await game_service.list_games(db, skip, limit)
    return GameListResponse(games=games, total=len(games))


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.patch("/{game_id}", response_model=GameResponse)
async def update_game(
    game_id: uuid.UUID,
    data: GameUpdate,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.status not in [GameStatus.DRAFT, GameStatus.PAUSED]:
        raise HTTPException(status_code=400, detail="Cannot update game in current state")
    
    return await game_service.update_game(db, game, data)


@router.post("/{game_id}/vulnbox")
async def upload_vulnbox(
    game_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.status != GameStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Can only upload vulnbox in draft state")
    
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a ZIP archive")
    
    content = await file.read()
    vulnbox_path = await docker_service.extract_vulnbox(game_id, content)
    await game_service.set_game_vulnbox_path(db, game, vulnbox_path)
    
    return {"message": "Vulnbox uploaded", "path": vulnbox_path}


@router.post("/{game_id}/checker")
async def upload_checker(
    game_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.status != GameStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Can only upload checker in draft state")
    
    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="File must be a Python file")
    
    settings = get_settings()
    checker_dir = Path(settings.upload_dir) / "checkers"
    checker_dir.mkdir(parents=True, exist_ok=True)
    
    checker_path = checker_dir / f"{game_id}_checker.py"
    content = await file.read()
    checker_path.write_bytes(content)
    
    module_name = f"uploads.checkers.{game_id}_checker"
    await game_service.set_game_checker_module(db, game, module_name)
    
    return {"message": "Checker uploaded", "module": module_name}


@router.post("/{game_id}/teams", response_model=GameTeamResponse)
async def add_team(
    game_id: uuid.UUID,
    data: GameTeamAdd,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_team = await game_service.add_team_to_game(db, game_id, data.team_id)
    return game_team


@router.get("/{game_id}/teams", response_model=list[GameTeamResponse])
async def get_game_teams(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return await game_service.get_game_teams(db, game_id)


@router.post("/{game_id}/start")
async def start_game(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.status not in [GameStatus.DRAFT, GameStatus.PAUSED]:
        raise HTTPException(status_code=400, detail="Game cannot be started in current state")
    
    if not game.vulnbox_path:
        raise HTTPException(status_code=400, detail="Vulnbox not uploaded")
    
    if not game.checker_module:
        raise HTTPException(status_code=400, detail="Checker not uploaded")
    
    teams = await game_service.get_game_teams(db, game_id)
    if not teams:
        raise HTTPException(status_code=400, detail="No teams in game")
    
    await game_service.update_game_status(db, game, GameStatus.DEPLOYING)
    
    image_tag = await docker_service.build_vulnbox_image(game_id, game.vulnbox_path)
    
    for team in teams:
        container_name, container_ip = await docker_service.deploy_team_container(
            game_id, team.team_id, image_tag
        )
        await game_service.update_game_team_container(db, team, container_name, container_ip)
    
    await game_service.update_game_status(db, game, GameStatus.RUNNING)
    
    return {"message": "Game started", "teams_deployed": len(teams)}


@router.post("/{game_id}/pause")
async def pause_game(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.status != GameStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Game is not running")
    
    await game_service.update_game_status(db, game, GameStatus.PAUSED)
    return {"message": "Game paused"}


@router.post("/{game_id}/stop")
async def stop_game(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    teams = await game_service.get_game_teams(db, game_id)
    for team in teams:
        if team.container_name:
            await docker_service.stop_team_container(team.container_name)
    
    await game_service.update_game_status(db, game, GameStatus.FINISHED)
    return {"message": "Game stopped", "containers_removed": len(teams)}
