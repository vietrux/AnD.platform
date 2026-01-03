import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.submission import SubmissionStatus


class FlagSubmit(BaseModel):
    game_id: uuid.UUID = Field(..., description="Game ID for validation")
    team_id: str = Field(..., min_length=1, description="Team identifier")
    flag: str = Field(..., min_length=1)


class SubmissionResponse(BaseModel):
    status: SubmissionStatus
    points: int
    message: str


class SubmissionHistoryItem(BaseModel):
    id: uuid.UUID
    submitted_flag: str
    status: SubmissionStatus
    points: int
    submitted_at: datetime

    class Config:
        from_attributes = True


class SubmissionHistoryResponse(BaseModel):
    submissions: list[SubmissionHistoryItem]
    total: int


class SubmissionDetailResponse(BaseModel):
    id: uuid.UUID
    game_id: uuid.UUID
    attacker_team_id: str
    flag_id: uuid.UUID | None
    submitted_flag: str
    status: SubmissionStatus
    points: int
    submitted_at: datetime

    class Config:
        from_attributes = True


class SubmissionListResponse(BaseModel):
    items: list[SubmissionDetailResponse]
    total: int
    skip: int
    limit: int
    has_more: bool
    
    @classmethod
    def create(
        cls,
        items: list[SubmissionDetailResponse],
        total: int,
        skip: int = 0,
        limit: int = 50,
    ) -> "SubmissionListResponse":
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total,
        )

