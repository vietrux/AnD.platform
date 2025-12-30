import uuid
from datetime import datetime
from pydantic import BaseModel

from src.models.service_status import CheckStatus
from src.schemas.common import PaginatedResponse


class ServiceStatusResponse(BaseModel):
    id: uuid.UUID
    game_id: uuid.UUID
    team_id: str
    tick_id: uuid.UUID
    status: CheckStatus
    sla_percentage: float
    error_message: str | None
    check_duration_ms: int | None
    checked_at: datetime

    class Config:
        from_attributes = True


class ServiceStatusListResponse(PaginatedResponse[ServiceStatusResponse]):
    pass
