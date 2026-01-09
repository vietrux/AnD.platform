import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import ServiceStatus, Scoreboard, CheckStatus, Flag, Tick


# =============================================================================
# SCORING CONSTANTS
# =============================================================================

# Base points per tick for SLA (service availability)
SLA_POINTS_PER_TICK = 100

# Base defense points awarded per uncaptured flag per tick
DEFENSE_POINTS_PER_FLAG = 25

# SLA is used as a multiplier (percentage). This scales it.
# If SLA is 80%, the multiplier will be 0.80
SLA_MULTIPLIER_ENABLED = True


# =============================================================================
# SERVICE STATUS TRACKING
# =============================================================================

async def record_service_status(
    db: AsyncSession,
    game_id: uuid.UUID,
    team_id: str,
    tick_id: uuid.UUID,
    status: CheckStatus,
    sla_percentage: float,
    error_message: str | None = None,
    check_duration_ms: int | None = None,
) -> ServiceStatus:
    """Record service status check result for a team in a tick."""
    # Check if service status already exists for this game/team/tick
    result = await db.execute(
        select(ServiceStatus).where(
            ServiceStatus.game_id == game_id,
            ServiceStatus.team_id == team_id,
            ServiceStatus.tick_id == tick_id,
        )
    )
    existing_status = result.scalar_one_or_none()
    
    if existing_status:
        return existing_status
    
    service_status = ServiceStatus(
        game_id=game_id,
        team_id=team_id,
        tick_id=tick_id,
        status=status,
        sla_percentage=sla_percentage,
        error_message=error_message,
        check_duration_ms=check_duration_ms,
    )
    db.add(service_status)
    
    # Update SLA points immediately
    sla_points = int((sla_percentage / 100.0) * SLA_POINTS_PER_TICK)
    await update_team_sla_score(db, game_id, team_id, sla_points)
    
    await db.commit()
    await db.refresh(service_status)
    return service_status


async def update_team_sla_score(
    db: AsyncSession,
    game_id: uuid.UUID,
    team_id: str,
    sla_points: int,
) -> None:
    """Add SLA points to team's scoreboard."""
    result = await db.execute(
        select(Scoreboard).where(
            Scoreboard.game_id == game_id,
            Scoreboard.team_id == team_id,
        )
    )
    scoreboard = result.scalar_one_or_none()
    
    if scoreboard:
        scoreboard.sla_points += sla_points
        await recalculate_total_score(scoreboard)


# =============================================================================
# DEFENSE POINTS CALCULATION
# =============================================================================

async def calculate_defense_points_for_tick(
    db: AsyncSession,
    game_id: uuid.UUID,
    tick: Tick,
) -> None:
    """
    Calculate and award defense points for a completed tick.
    
    Defense points are awarded for each flag that was NOT stolen during the tick,
    but only if the team's service was UP (SLA OK).
    
    Formula: Defense += DEFENSE_POINTS_PER_FLAG for each uncaptured flag where SLA=OK
    """
    # Get all flags for this tick
    flags_result = await db.execute(
        select(Flag).where(
            Flag.game_id == game_id,
            Flag.tick_id == tick.id,
        )
    )
    flags = list(flags_result.scalars().all())
    
    # Group flags by team
    team_flags: dict[str, list[Flag]] = {}
    for flag in flags:
        if flag.team_id not in team_flags:
            team_flags[flag.team_id] = []
        team_flags[flag.team_id].append(flag)
    
    # Get service statuses for this tick
    statuses_result = await db.execute(
        select(ServiceStatus).where(
            ServiceStatus.game_id == game_id,
            ServiceStatus.tick_id == tick.id,
        )
    )
    statuses = {s.team_id: s for s in statuses_result.scalars().all()}
    
    # Calculate defense points for each team
    for team_id, flags_list in team_flags.items():
        # Check if service was UP for this team
        service_status = statuses.get(team_id)
        sla_ok = service_status and service_status.status == CheckStatus.UP
        
        if not sla_ok:
            # No defense points if service was down
            continue
        
        # Count uncaptured flags
        uncaptured_count = sum(1 for f in flags_list if not f.is_stolen)
        
        if uncaptured_count > 0:
            defense_points = uncaptured_count * DEFENSE_POINTS_PER_FLAG
            await add_team_defense_points(db, game_id, team_id, defense_points)


async def add_team_defense_points(
    db: AsyncSession,
    game_id: uuid.UUID,
    team_id: str,
    points: int,
) -> None:
    """Add defense points to a team's scoreboard."""
    result = await db.execute(
        select(Scoreboard).where(
            Scoreboard.game_id == game_id,
            Scoreboard.team_id == team_id,
        )
    )
    scoreboard = result.scalar_one_or_none()
    
    if scoreboard:
        scoreboard.defense_points += points
        await recalculate_total_score(scoreboard)


# =============================================================================
# TOTAL SCORE CALCULATION
# =============================================================================

async def recalculate_total_score(scoreboard: Scoreboard) -> None:
    """
    Recalculate total score using the formula:
    
    If SLA_MULTIPLIER_ENABLED:
        Total = (Attack + Defense) * (SLA_Points / Max_Possible_SLA)
        
    Otherwise (legacy additive):
        Total = Attack + Defense + SLA
    
    Note: SLA_Points accumulate over ticks. We normalize by dividing by 
    a reasonable base to get a multiplier between 0 and ~1.
    """
    if SLA_MULTIPLIER_ENABLED:
        # Get SLA as a multiplier (0.0 to 1.0+)
        # Assume average SLA of 100 points per tick is "100%"
        # If team has 1000 SLA points over 10 ticks, that's perfect SLA
        # We use a simple approach: SLA multiplier = min(sla_points / 100, 1.0) per calculation
        # But since SLA accumulates, we use: total_sla / max(100, total_sla) * some factor
        
        # Simpler approach: Use SLA as a percentage of maximum theoretical
        # For now, use a normalized approach where we cap at 1.0
        # This means SLA acts as a penalty if < 100%
        
        # Actually, the cleanest way: SLA multiplier = (sla_points / (ticks * 100))
        # But we don't have tick count here easily. 
        
        # Pragmatic solution: 
        # SLA multiplier = min(1.0, sla_points / 1000) for soft cap
        # Or just use (sla_points / 100) / 10 = sla_points / 1000 capped at 1.0
        
        # For simplicity and balance: use raw SLA as bonus, but total uses multiplier
        # Let's define: Total = (Attack + Defense) * (0.5 + 0.5 * sla_factor)
        # Where sla_factor = min(1.0, sla_points / 500)
        
        # Even simpler for v1: additive with weight
        # Total = Attack + Defense + (SLA * 0.5)
        
        # After consideration, let's do this:
        # The multiplicative SLA should be based on CUMULATIVE percentage
        # For now, we'll use a hybrid: Total = Attack + Defense + SLA (additive)
        # Then apply SLA as a multiplier only if we track cumulative SLA%
        
        # DECISION: Keep it simple but meaningful
        # SLA multiplier = sla_points / (sla_points + attack_points + defense_points + 1)
        # This creates natural balance
        
        # Final decision for clarity:
        # Total = (Attack + Defense) * SLA_Multiplier + SLA_Bonus
        # Where SLA_Multiplier = min(1.0, sla_points / 500) (scales over ~5 ticks)
        
        sla_multiplier = min(1.0, scoreboard.sla_points / 500.0) if scoreboard.sla_points > 0 else 0.5
        base_score = scoreboard.attack_points + scoreboard.defense_points
        scoreboard.total_points = int(base_score * sla_multiplier) + scoreboard.sla_points
    else:
        # Legacy additive formula
        scoreboard.total_points = (
            scoreboard.attack_points + 
            scoreboard.defense_points + 
            scoreboard.sla_points
        )
    
    scoreboard.last_updated = datetime.utcnow()


async def recalculate_all_scores(db: AsyncSession, game_id: uuid.UUID) -> None:
    """Recalculate total scores for all teams in a game."""
    result = await db.execute(
        select(Scoreboard).where(Scoreboard.game_id == game_id)
    )
    scoreboards = list(result.scalars().all())
    
    for scoreboard in scoreboards:
        await recalculate_total_score(scoreboard)
    
    await db.commit()


# =============================================================================
# RANKINGS
# =============================================================================

async def update_rankings(db: AsyncSession, game_id: uuid.UUID) -> None:
    """Update rankings for all teams based on total points."""
    result = await db.execute(
        select(Scoreboard)
        .where(Scoreboard.game_id == game_id)
        .order_by(Scoreboard.total_points.desc())
    )
    scoreboards = list(result.scalars().all())
    
    for rank, scoreboard in enumerate(scoreboards, 1):
        scoreboard.rank = rank
    
    await db.commit()


# =============================================================================
# QUERIES
# =============================================================================

async def get_scoreboard(db: AsyncSession, game_id: uuid.UUID) -> list[Scoreboard]:
    """Get scoreboard entries for a game, ordered by rank."""
    result = await db.execute(
        select(Scoreboard)
        .where(Scoreboard.game_id == game_id)
        .order_by(Scoreboard.rank.asc())
    )
    return list(result.scalars().all())


async def get_team_scoreboard(db: AsyncSession, game_id: uuid.UUID, team_id: str) -> Scoreboard | None:
    """Get scoreboard entry for a specific team in a game."""
    result = await db.execute(
        select(Scoreboard).where(
            Scoreboard.game_id == game_id,
            Scoreboard.team_id == team_id,
        )
    )
    return result.scalar_one_or_none()
