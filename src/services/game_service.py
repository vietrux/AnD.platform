import uuid
import secrets
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Game, GameTeam, GameStatus, Scoreboard
from src.schemas import GameCreate, GameUpdate


async def create_game(db: AsyncSession, data: GameCreate) -> Game:
    game = Game(
        name=data.name,
        description=data.description,
        tick_duration_seconds=data.tick_duration_seconds,
        status=GameStatus.DRAFT,
    )
    db.add(game)
    await db.commit()
    await db.refresh(game)
    return game


async def get_game(db: AsyncSession, game_id: uuid.UUID) -> Game | None:
    result = await db.execute(select(Game).where(Game.id == game_id))
    return result.scalar_one_or_none()


async def get_game_by_name(db: AsyncSession, name: str) -> Game | None:
    result = await db.execute(select(Game).where(Game.name == name))
    return result.scalar_one_or_none()


async def list_games(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[Game]:
    result = await db.execute(select(Game).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_game(db: AsyncSession, game: Game, data: GameUpdate) -> Game:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(game, field, value)
    await db.commit()
    await db.refresh(game)
    return game


async def update_game_status(db: AsyncSession, game: Game, status: GameStatus) -> Game:
    game.status = status
    if status == GameStatus.RUNNING and game.start_time is None:
        game.start_time = datetime.utcnow()
    elif status == GameStatus.FINISHED:
        game.end_time = datetime.utcnow()
    await db.commit()
    await db.refresh(game)
    return game


async def set_game_vulnbox_path(db: AsyncSession, game: Game, path: str) -> Game:
    game.vulnbox_path = path
    await db.commit()
    await db.refresh(game)
    return game


async def set_game_checker_module(db: AsyncSession, game: Game, module: str) -> Game:
    game.checker_module = module
    await db.commit()
    await db.refresh(game)
    return game


async def add_team_to_game(db: AsyncSession, game_id: uuid.UUID, team_id: str) -> GameTeam:
    token = secrets.token_hex(32)
    game_team = GameTeam(
        game_id=game_id,
        team_id=team_id,
        token=token,
    )
    db.add(game_team)
    
    scoreboard = Scoreboard(
        game_id=game_id,
        team_id=team_id,
    )
    db.add(scoreboard)
    
    await db.commit()
    await db.refresh(game_team)
    return game_team


async def get_game_team_by_token(db: AsyncSession, token: str) -> GameTeam | None:
    result = await db.execute(select(GameTeam).where(GameTeam.token == token))
    return result.scalar_one_or_none()


async def get_game_teams(db: AsyncSession, game_id: uuid.UUID) -> list[GameTeam]:
    result = await db.execute(
        select(GameTeam).where(GameTeam.game_id == game_id, GameTeam.is_active == True)
    )
    return list(result.scalars().all())


async def update_game_team_container(
    db: AsyncSession, 
    game_team: GameTeam, 
    container_name: str, 
    container_ip: str,
    ssh_username: str | None = None,
    ssh_password: str | None = None,
    ssh_port: int | None = None,
) -> GameTeam:
    game_team.container_name = container_name
    game_team.container_ip = container_ip
    game_team.ssh_username = ssh_username
    game_team.ssh_password = ssh_password
    game_team.ssh_port = ssh_port
    await db.commit()
    await db.refresh(game_team)
    return game_team
