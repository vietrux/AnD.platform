import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.submission import SubmissionStatus


class FlagSubmit(BaseModel):
    team_token: str = Field(..., min_length=1)
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
