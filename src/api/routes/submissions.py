import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_db, GameNotFoundError, SubmissionNotFoundError
from src.models import SubmissionStatus
from src.schemas import FlagSubmit, SubmissionResponse, DeleteResponse
from src.schemas.submission import SubmissionDetailResponse, SubmissionListResponse
from src.services import submission_service, game_service


router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionResponse)
async def submit_flag(
    data: FlagSubmit,
    db: AsyncSession = Depends(get_db),
):
    status, points, message = await submission_service.submit_flag(
        db=db,
        game_id=data.game_id,
        team_id=data.team_id,
        submitted_flag=data.flag,
    )
    
    return SubmissionResponse(
        status=status,
        points=points,
        message=message,
    )


@router.get("", response_model=SubmissionListResponse)
async def list_submissions(
    game_id: uuid.UUID | None = Query(None, description="Filter by game ID"),
    team_id: str | None = Query(None, description="Filter by team ID"),
    status: SubmissionStatus | None = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    if game_id:
        game = await game_service.get_game(db, game_id)
        if not game:
            raise GameNotFoundError().to_http_exception()
    
    submissions = await submission_service.list_submissions(
        db, game_id, team_id, status, skip, limit
    )
    total = await submission_service.count_submissions(db, game_id, team_id, status)
    
    return SubmissionListResponse.create(
        items=[SubmissionDetailResponse.model_validate(s) for s in submissions],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{submission_id}", response_model=SubmissionDetailResponse)
async def get_submission(
    submission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    submission = await submission_service.get_submission(db, submission_id)
    if not submission:
        raise SubmissionNotFoundError().to_http_exception()
    
    return submission


@router.delete("/{submission_id}", response_model=DeleteResponse)
async def delete_submission(
    submission_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    submission = await submission_service.get_submission(db, submission_id)
    if not submission:
        raise SubmissionNotFoundError().to_http_exception()
    
    await submission_service.delete_submission(db, submission_id)
    return DeleteResponse(deleted_id=submission_id)

