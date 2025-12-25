import uuid
from datetime import datetime
from pydantic import BaseModel


class ScoreboardEntry(BaseModel):
    team_id: str
    attack_points: int
    defense_points: int
    sla_points: int
    total_points: int
    rank: int
    flags_captured: int
    flags_lost: int

    class Config:
        from_attributes = True


class ScoreboardResponse(BaseModel):
    game_id: uuid.UUID
    game_name: str
    current_tick: int
    entries: list[ScoreboardEntry]
    last_updated: datetime | None
