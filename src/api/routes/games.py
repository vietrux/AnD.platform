import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_db, get_settings, CannotDeleteRunningGameError, TeamNotFoundError
from src.models import GameStatus
from src.schemas import (
    GameCreate,
    GameUpdate,
    GameTeamAdd,
    GameTeamUpdate,
    GameResponse,
    GameTeamResponse,
    GameListResponse,
    DeleteResponse,
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
    
    settings = get_settings()
    team_credentials = []
    
    for idx, team in enumerate(teams):
        ssh_port = settings.ssh_port_base + idx + 1
        ssh_username, ssh_password = docker_service.generate_ssh_credentials()
        
        container_name, container_ip = await docker_service.deploy_team_container(
            game_id, team.team_id, image_tag, ssh_port, ssh_username, ssh_password
        )
        
        await game_service.update_game_team_container(
            db, team, container_name, container_ip, ssh_username, ssh_password, ssh_port
        )
        
        team_credentials.append({
            "team_id": team.team_id,
            "container_ip": container_ip,
            "ssh_host": settings.ssh_host,
            "ssh_port": ssh_port,
            "ssh_username": ssh_username,
            "ssh_password": ssh_password,
        })
    
    await game_service.update_game_status(db, game, GameStatus.RUNNING)
    
    return {
        "message": "Game started",
        "teams_deployed": len(teams),
        "teams": team_credentials,
    }


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


@router.delete("/{game_id}", response_model=DeleteResponse)
async def delete_game(
    game_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.status in [GameStatus.RUNNING, GameStatus.DEPLOYING]:
        raise CannotDeleteRunningGameError().to_http_exception()
    
    teams = await game_service.get_game_teams(db, game_id)
    for team in teams:
        if team.container_name:
            await docker_service.stop_team_container(team.container_name)
    
    await game_service.delete_game(db, game_id)
    return DeleteResponse(deleted_id=game_id)


@router.get("/{game_id}/teams/{team_id}", response_model=GameTeamResponse)
async def get_game_team(
    game_id: uuid.UUID,
    team_id: str,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_team = await game_service.get_game_team(db, game_id, team_id)
    if not game_team:
        raise TeamNotFoundError().to_http_exception()
    
    return game_team


@router.patch("/{game_id}/teams/{team_id}", response_model=GameTeamResponse)
async def update_game_team(
    game_id: uuid.UUID,
    team_id: str,
    data: GameTeamUpdate,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_team = await game_service.get_game_team(db, game_id, team_id)
    if not game_team:
        raise TeamNotFoundError().to_http_exception()
    
    return await game_service.update_game_team(db, game_team, data)


@router.delete("/{game_id}/teams/{team_id}", response_model=DeleteResponse)
async def remove_team(
    game_id: uuid.UUID,
    team_id: str,
    db: AsyncSession = Depends(get_db),
):
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    game_team = await game_service.get_game_team(db, game_id, team_id)
    if not game_team:
        raise TeamNotFoundError().to_http_exception()
    
    if game_team.container_name:
        await docker_service.stop_team_container(game_team.container_name)
    
    await game_service.delete_game_team(db, game_id, team_id)
    return DeleteResponse(deleted_id=game_team.id)


@router.post("/{game_id}/assign-vulnbox", response_model=GameResponse)
async def assign_vulnbox(
    game_id: uuid.UUID,
    vulnbox_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    from src.services import vulnbox_service
    
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.status != GameStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Can only assign vulnbox in draft state")
    
    vulnbox = await vulnbox_service.get_vulnbox(db, vulnbox_id)
    if not vulnbox:
        raise HTTPException(status_code=404, detail="Vulnbox not found")
    
    return await game_service.assign_vulnbox(db, game, vulnbox)


@router.post("/{game_id}/assign-checker", response_model=GameResponse)
async def assign_checker(
    game_id: uuid.UUID,
    checker_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    from src.services import checker_crud_service
    
    game = await game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game.status != GameStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Can only assign checker in draft state")
    
    checker = await checker_crud_service.get_checker(db, checker_id)
    if not checker:
        raise HTTPException(status_code=404, detail="Checker not found")
    
    return await game_service.assign_checker(db, game, checker)

