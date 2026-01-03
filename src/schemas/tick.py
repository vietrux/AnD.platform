import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.tick import TickStatus
from src.schemas.common import PaginatedResponse


class TickCreate(BaseModel):
    game_id: uuid.UUID
    tick_number: int


class TickResponse(BaseModel):

    id: uuid.UUID
    game_id: uuid.UUID
    tick_number: int
    status: TickStatus
    flags_placed: int
    started_at: datetime | None = Field(None, validation_alias="start_time")
    completed_at: datetime | None = Field(None, validation_alias="end_time")
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class TickUpdate(BaseModel):
    status: TickStatus | None = None


class TickListResponse(PaginatedResponse[TickResponse]):
    pass
