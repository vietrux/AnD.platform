import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (
    Flag, 
    FlagSubmission, 
    SubmissionStatus, 
    GameTeam,
    Scoreboard,
    FlagType,
)
from src.services import flag_service


USER_FLAG_POINTS = 50
ROOT_FLAG_POINTS = 150


async def submit_flag(
    db: AsyncSession,
    game_id: uuid.UUID,
    team_id: str,
    submitted_flag: str,
) -> tuple[SubmissionStatus, int, str]:
    game_team = await db.execute(
        select(GameTeam).where(
            GameTeam.game_id == game_id,
            GameTeam.team_id == team_id,
            GameTeam.is_active == True
        )
    )
    game_team = game_team.scalar_one_or_none()
    
    if not game_team:
        return SubmissionStatus.INVALID, 0, "Team not found in game"
    
    flag = await flag_service.get_flag_by_value(db, submitted_flag)
    
    if not flag:
        submission = FlagSubmission(
            game_id=game_team.game_id,
            attacker_team_id=game_team.team_id,
            submitted_flag=submitted_flag,
            status=SubmissionStatus.INVALID,
            points=0,
        )
        db.add(submission)
        await db.commit()
        return SubmissionStatus.INVALID, 0, "Invalid flag"
    
    if flag.game_id != game_team.game_id:
        return SubmissionStatus.INVALID, 0, "Flag not from this game"
    
    if flag.team_id == game_team.team_id:
        submission = FlagSubmission(
            game_id=game_team.game_id,
            attacker_team_id=game_team.team_id,
            flag_id=flag.id,
            submitted_flag=submitted_flag,
            status=SubmissionStatus.OWN_FLAG,
            points=0,
        )
        db.add(submission)
        await db.commit()
        return SubmissionStatus.OWN_FLAG, 0, "Cannot submit your own flag"
    
    if flag.valid_until < datetime.utcnow():
        submission = FlagSubmission(
            game_id=game_team.game_id,
            attacker_team_id=game_team.team_id,
            flag_id=flag.id,
            submitted_flag=submitted_flag,
            status=SubmissionStatus.EXPIRED,
            points=0,
        )
        db.add(submission)
        await db.commit()
        return SubmissionStatus.EXPIRED, 0, "Flag expired"
    
    existing = await db.execute(
        select(FlagSubmission).where(
            FlagSubmission.attacker_team_id == game_team.team_id,
            FlagSubmission.flag_id == flag.id,
            FlagSubmission.status == SubmissionStatus.ACCEPTED,
        )
    )
    if existing.scalar_one_or_none():
        submission = FlagSubmission(
            game_id=game_team.game_id,
            attacker_team_id=game_team.team_id,
            flag_id=flag.id,
            submitted_flag=submitted_flag,
            status=SubmissionStatus.DUPLICATE,
            points=0,
        )
        db.add(submission)
        await db.commit()
        return SubmissionStatus.DUPLICATE, 0, "Flag already submitted"
    
    points = ROOT_FLAG_POINTS if flag.flag_type == FlagType.ROOT else USER_FLAG_POINTS
    
    submission = FlagSubmission(
        game_id=game_team.game_id,
        attacker_team_id=game_team.team_id,
        flag_id=flag.id,
        submitted_flag=submitted_flag,
        status=SubmissionStatus.ACCEPTED,
        points=points,
    )
    db.add(submission)
    
    await flag_service.mark_flag_stolen(db, flag)
    
    await update_team_attack_score(db, game_team.game_id, game_team.team_id, points)
    await update_team_defense_score(db, flag.game_id, flag.team_id)
    
    await db.commit()
    return SubmissionStatus.ACCEPTED, points, f"Flag accepted! +{points} points"


async def update_team_attack_score(
    db: AsyncSession,
    game_id: uuid.UUID,
    team_id: str,
    points: int,
) -> None:
    result = await db.execute(
        select(Scoreboard).where(
            Scoreboard.game_id == game_id,
            Scoreboard.team_id == team_id,
        )
    )
    scoreboard = result.scalar_one_or_none()
    
    if scoreboard:
        scoreboard.attack_points += points
        scoreboard.flags_captured += 1
        scoreboard.total_points = (
            scoreboard.attack_points + 
            scoreboard.defense_points + 
            scoreboard.sla_points
        )
        scoreboard.last_updated = datetime.utcnow()


async def update_team_defense_score(
    db: AsyncSession,
    game_id: uuid.UUID,
    team_id: str,
) -> None:
    result = await db.execute(
        select(Scoreboard).where(
            Scoreboard.game_id == game_id,
            Scoreboard.team_id == team_id,
        )
    )
    scoreboard = result.scalar_one_or_none()
    
    if scoreboard:
        scoreboard.flags_lost += 1
        scoreboard.last_updated = datetime.utcnow()


async def list_submissions(
    db: AsyncSession,
    game_id: uuid.UUID | None = None,
    team_id: str | None = None,
    status: SubmissionStatus | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[FlagSubmission]:
    query = select(FlagSubmission)
    
    if game_id:
        query = query.where(FlagSubmission.game_id == game_id)
    if team_id:
        query = query.where(FlagSubmission.attacker_team_id == team_id)
    if status:
        query = query.where(FlagSubmission.status == status)
    
    query = query.order_by(FlagSubmission.submitted_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_submission(
    db: AsyncSession, submission_id: uuid.UUID
) -> FlagSubmission | None:
    result = await db.execute(
        select(FlagSubmission).where(FlagSubmission.id == submission_id)
    )
    return result.scalar_one_or_none()


async def count_submissions(
    db: AsyncSession,
    game_id: uuid.UUID | None = None,
    team_id: str | None = None,
    status: SubmissionStatus | None = None,
) -> int:
    query = select(func.count(FlagSubmission.id))
    
    if game_id:
        query = query.where(FlagSubmission.game_id == game_id)
    if team_id:
        query = query.where(FlagSubmission.attacker_team_id == team_id)
    if status:
        query = query.where(FlagSubmission.status == status)
    
    result = await db.execute(query)
    return result.scalar() or 0


async def delete_submission(
    db: AsyncSession, submission_id: uuid.UUID
) -> bool:
    submission = await get_submission(db, submission_id)
    if submission:
        await db.delete(submission)
        await db.commit()
        return True
    return False

