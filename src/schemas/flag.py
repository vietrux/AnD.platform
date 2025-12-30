import uuid
from datetime import datetime
from pydantic import BaseModel

from src.models.flag import FlagType
from src.schemas.common import PaginatedResponse


class FlagResponse(BaseModel):
    id: uuid.UUID
    game_id: uuid.UUID
    team_id: str
    tick_id: uuid.UUID
    flag_value: str
    flag_type: FlagType
    is_stolen: bool
    stolen_count: int
    expires_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class FlagUpdate(BaseModel):
    is_stolen: bool | None = None


class FlagListResponse(PaginatedResponse[FlagResponse]):
    pass
