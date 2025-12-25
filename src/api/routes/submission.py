from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import get_db
from src.schemas import FlagSubmit, SubmissionResponse
from src.services import submission_service


router = APIRouter(prefix="/submit", tags=["submission"])


@router.post("", response_model=SubmissionResponse)
async def submit_flag(
    data: FlagSubmit,
    db: AsyncSession = Depends(get_db),
):
    status, points, message = await submission_service.submit_flag(
        db=db,
        team_token=data.team_token,
        submitted_flag=data.flag,
    )
    
    return SubmissionResponse(
        status=status,
        points=points,
        message=message,
    )
