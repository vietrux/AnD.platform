"""
Port Allocation Service

Manages SSH port allocation across multiple concurrent games to prevent port collisions.

Design:
- Each game gets a dedicated port range based on game creation order
- Ports are calculated per-game to avoid conflicts with other running games
- Uses database to query active games and their team counts
"""
import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Game, GameTeam, GameStatus
from src.core.config import get_settings


# Port range configuration
# Each game gets up to MAX_TEAMS_PER_GAME ports
MAX_TEAMS_PER_GAME = 50


async def get_game_port_base(db: AsyncSession, game_id: uuid.UUID) -> int:
    """
    Calculate the base port for a specific game.
    
    This uses the game's position among all games to assign a unique port range.
    Each game gets MAX_TEAMS_PER_GAME ports starting from:
    ssh_port_base + (game_index * MAX_TEAMS_PER_GAME)
    
    Returns:
        Base port number for this game's teams
    """
    settings = get_settings()
    
    # Get all games ordered by creation time to determine this game's index
    result = await db.execute(
        select(Game.id, Game.created_at)
        .order_by(Game.created_at)
    )
    all_games = result.all()
    
    # Find this game's index
    game_index = 0
    for idx, (gid, _) in enumerate(all_games):
        if gid == game_id:
            game_index = idx
            break
    
    return settings.ssh_port_base + (game_index * MAX_TEAMS_PER_GAME)


async def get_port_for_team(db: AsyncSession, game_id: uuid.UUID, team_index: int) -> int:
    """
    Get the SSH port for a specific team in a game.
    
    Args:
        db: Database session
        game_id: Game UUID
        team_index: 0-based index of the team in the game
        
    Returns:
        SSH port number for this team
    """
    game_base = await get_game_port_base(db, game_id)
    return game_base + team_index + 1


async def get_ports_for_game(db: AsyncSession, game_id: uuid.UUID, team_count: int) -> list[int]:
    """
    Get all SSH ports for a game.
    
    Args:
        db: Database session
        game_id: Game UUID
        team_count: Number of teams in the game
        
    Returns:
        List of SSH port numbers for each team (0-indexed)
    """
    if team_count > MAX_TEAMS_PER_GAME:
        raise ValueError(f"Game cannot have more than {MAX_TEAMS_PER_GAME} teams")
    
    game_base = await get_game_port_base(db, game_id)
    return [game_base + i + 1 for i in range(team_count)]


async def check_port_conflicts(db: AsyncSession, game_id: uuid.UUID, team_count: int) -> list[dict]:
    """
    Check if starting a game would cause port conflicts with running games.
    
    This is a safety check before deploying containers.
    
    Returns:
        List of conflicts (empty if no conflicts)
    """
    settings = get_settings()
    proposed_ports = await get_ports_for_game(db, game_id, team_count)
    
    # Get all running/deploying games (excluding this one)
    result = await db.execute(
        select(GameTeam.ssh_port, GameTeam.game_id, GameTeam.team_id)
        .join(Game)
        .where(
            Game.status.in_([GameStatus.RUNNING, GameStatus.DEPLOYING, GameStatus.PAUSED]),
            GameTeam.ssh_port.isnot(None),
            Game.id != game_id,
        )
    )
    used_ports = result.all()
    
    conflicts = []
    used_port_set = {port for port, _, _ in used_ports}
    
    for port in proposed_ports:
        if port in used_port_set:
            # Find which game is using this port
            for used_port, gid, tid in used_ports:
                if used_port == port:
                    conflicts.append({
                        "port": port,
                        "used_by_game": str(gid),
                        "used_by_team": tid,
                    })
                    break
    
    return conflicts


async def get_available_ports_summary(db: AsyncSession) -> dict:
    """
    Get a summary of port allocation status.
    
    Useful for debugging and monitoring.
    """
    settings = get_settings()
    
    # Get all running games with their port usage
    result = await db.execute(
        select(
            Game.id,
            Game.name,
            Game.status,
            func.count(GameTeam.id).label("team_count"),
            func.min(GameTeam.ssh_port).label("min_port"),
            func.max(GameTeam.ssh_port).label("max_port"),
        )
        .outerjoin(GameTeam)
        .where(Game.status.in_([GameStatus.RUNNING, GameStatus.DEPLOYING, GameStatus.PAUSED]))
        .group_by(Game.id, Game.name, Game.status)
    )
    
    games = result.all()
    
    return {
        "base_port": settings.ssh_port_base,
        "max_teams_per_game": MAX_TEAMS_PER_GAME,
        "active_games": [
            {
                "game_id": str(g.id),
                "game_name": g.name,
                "status": g.status,
                "team_count": g.team_count,
                "port_range": f"{g.min_port}-{g.max_port}" if g.min_port else "none",
            }
            for g in games
        ],
        "total_active_games": len(games),
    }
