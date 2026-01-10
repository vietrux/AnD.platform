import uuid
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
        max_ticks=data.max_ticks,
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
    """Update game status with proper pause time tracking.
    
    When resuming from pause, adjusts current_tick_started_at to maintain
    proper tick timing (ticks continue from where they left off).
    """
    from datetime import timedelta
    now = datetime.utcnow()
    
    if status == GameStatus.RUNNING:
        if game.start_time is None:
            # First time starting
            game.start_time = now
            game.current_tick_started_at = now
        elif game.status == GameStatus.PAUSED and game.paused_at:
            # Resuming from pause: accumulate paused duration
            paused_duration = (now - game.paused_at).total_seconds()
            game.total_paused_seconds = (game.total_paused_seconds or 0.0) + paused_duration
            
            # Adjust tick start time - shift forward by paused duration
            # This ensures the tick timer continues from where it was paused
            if game.current_tick_started_at:
                game.current_tick_started_at = game.current_tick_started_at + timedelta(seconds=paused_duration)
            
            game.paused_at = None
            
    elif status == GameStatus.PAUSED:
        # Record when game was paused
        game.paused_at = now
        
    elif status == GameStatus.FINISHED:
        game.end_time = now
        # Clear pause tracking
        game.paused_at = None
    
    game.status = status
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
    """Add a team to a game. Returns existing entry if team is already in the game."""
    # Check if team is already in this game
    existing = await db.execute(
        select(GameTeam).where(
            GameTeam.game_id == game_id,
            GameTeam.team_id == team_id,
        )
    )
    existing_game_team = existing.scalar_one_or_none()
    if existing_game_team:
        # Team already in game, return existing entry
        return existing_game_team
    
    game_team = GameTeam(
        game_id=game_id,
        team_id=team_id,
    )
    db.add(game_team)
    
    # Check if scoreboard entry exists
    existing_scoreboard = await db.execute(
        select(Scoreboard).where(
            Scoreboard.game_id == game_id,
            Scoreboard.team_id == team_id,
        )
    )
    if not existing_scoreboard.scalar_one_or_none():
        scoreboard = Scoreboard(
            game_id=game_id,
            team_id=team_id,
        )
        db.add(scoreboard)
    
    await db.commit()
    await db.refresh(game_team)
    return game_team


async def get_running_games_for_team(db: AsyncSession, team_id: str) -> list[Game]:
    """Get all running/deploying games that a team is currently in.
    
    Used to prevent a team from being in multiple active games simultaneously.
    """
    result = await db.execute(
        select(Game)
        .join(GameTeam, Game.id == GameTeam.game_id)
        .where(
            GameTeam.team_id == team_id,
            GameTeam.is_active == True,
            Game.status.in_([GameStatus.RUNNING, GameStatus.DEPLOYING])
        )
    )
    return list(result.scalars().all())


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


async def delete_game(db: AsyncSession, game_id: uuid.UUID) -> bool:
    game = await get_game(db, game_id)
    if game:
        await db.delete(game)
        await db.commit()
        return True
    return False


async def get_game_team(
    db: AsyncSession, game_id: uuid.UUID, team_id: str
) -> GameTeam | None:
    result = await db.execute(
        select(GameTeam).where(
            GameTeam.game_id == game_id, 
            GameTeam.team_id == team_id
        )
    )
    return result.scalar_one_or_none()


async def update_game_team(
    db: AsyncSession, game_team: GameTeam, data
) -> GameTeam:
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(game_team, field, value)
    await db.commit()
    await db.refresh(game_team)
    return game_team


async def delete_game_team(
    db: AsyncSession, game_id: uuid.UUID, team_id: str
) -> bool:
    """Delete a team from a game (hard delete) and its associated scoreboard entry."""
    game_team = await get_game_team(db, game_id, team_id)
    if game_team:
        # Delete associated scoreboard entry
        result = await db.execute(
            select(Scoreboard).where(
                Scoreboard.game_id == game_id,
                Scoreboard.team_id == team_id,
            )
        )
        scoreboard = result.scalar_one_or_none()
        if scoreboard:
            await db.delete(scoreboard)
        
        # Hard delete the team
        await db.delete(game_team)
        await db.commit()
        return True
    return False


async def assign_vulnbox(db: AsyncSession, game: Game, vulnbox) -> Game:
    game.vulnbox_id = vulnbox.id
    game.vulnbox_path = vulnbox.path
    await db.commit()
    await db.refresh(game)
    return game


async def assign_checker(db: AsyncSession, game: Game, checker) -> Game:
    game.checker_id = checker.id
    game.checker_module = checker.module_name
    await db.commit()
    await db.refresh(game)
    return game


async def add_vulnbox_to_game(db: AsyncSession, game_id: uuid.UUID, vulnbox) -> "GameVulnbox":
    """Add a vulnbox to a game using the junction table."""
    from src.models import GameVulnbox
    
    # Check if already exists
    existing = await db.execute(
        select(GameVulnbox).where(
            GameVulnbox.game_id == game_id,
            GameVulnbox.vulnbox_id == vulnbox.id,
        )
    )
    existing_gv = existing.scalar_one_or_none()
    if existing_gv:
        return existing_gv
    
    game_vulnbox = GameVulnbox(
        game_id=game_id,
        vulnbox_id=vulnbox.id,
        vulnbox_path=vulnbox.path,
    )
    db.add(game_vulnbox)
    
    # Also update the game's primary vulnbox if not set
    game = await get_game(db, game_id)
    if game and not game.vulnbox_id:
        game.vulnbox_id = vulnbox.id
        game.vulnbox_path = vulnbox.path
    
    await db.commit()
    await db.refresh(game_vulnbox)
    return game_vulnbox


async def get_game_vulnboxes(db: AsyncSession, game_id: uuid.UUID) -> list["GameVulnbox"]:
    """Get all vulnboxes assigned to a game."""
    from src.models import GameVulnbox
    
    result = await db.execute(
        select(GameVulnbox).where(GameVulnbox.game_id == game_id)
    )
    return list(result.scalars().all())


async def remove_vulnbox_from_game(db: AsyncSession, game_id: uuid.UUID, vulnbox_id: uuid.UUID) -> bool:
    """Remove a vulnbox from a game."""
    from src.models import GameVulnbox
    
    result = await db.execute(
        select(GameVulnbox).where(
            GameVulnbox.game_id == game_id,
            GameVulnbox.vulnbox_id == vulnbox_id,
        )
    )
    game_vulnbox = result.scalar_one_or_none()
    
    if game_vulnbox:
        await db.delete(game_vulnbox)
        await db.commit()
        return True
    return False
