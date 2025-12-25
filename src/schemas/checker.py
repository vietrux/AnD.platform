import uuid
from pydantic import BaseModel, Field

from src.models.service_status import CheckStatus


class CheckerStatusSubmit(BaseModel):
    game_id: uuid.UUID
    team_id: str = Field(..., min_length=1)
    tick_id: uuid.UUID
    status: CheckStatus
    sla_percentage: float = Field(default=100.0, ge=0.0, le=100.0)
    message: str | None = None
    check_duration_ms: int | None = None


class CheckerStatusResponse(BaseModel):
    success: bool
    message: str
