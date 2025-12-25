import uuid
from datetime import datetime
from pydantic import BaseModel, Field

from src.models.game import GameStatus


class GameCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    tick_duration_seconds: int = Field(default=60, ge=10, le=600)


class GameUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    tick_duration_seconds: int | None = None


class GameTeamAdd(BaseModel):
    team_id: str = Field(..., min_length=1, max_length=100)


class GameResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    vulnbox_path: str | None
    checker_module: str | None
    status: GameStatus
    tick_duration_seconds: int
    current_tick: int
    start_time: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class GameTeamResponse(BaseModel):
    id: uuid.UUID
    game_id: uuid.UUID
    team_id: str
    container_name: str | None
    container_ip: str | None
    token: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class GameListResponse(BaseModel):
    games: list[GameResponse]
    total: int
