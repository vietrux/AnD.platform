import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class Scoreboard(Base):
    __tablename__ = "scoreboard"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    team_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    attack_points: Mapped[int] = mapped_column(Integer, default=0)
    defense_points: Mapped[int] = mapped_column(Integer, default=0)
    sla_points: Mapped[int] = mapped_column(Integer, default=0)
    total_points: Mapped[int] = mapped_column(Integer, default=0, index=True)
    
    rank: Mapped[int] = mapped_column(Integer, default=0)
    
    flags_captured: Mapped[int] = mapped_column(Integer, default=0)
    flags_lost: Mapped[int] = mapped_column(Integer, default=0)
    
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_scoreboard_game_team", "game_id", "team_id", unique=True),
        Index("ix_scoreboard_game_rank", "game_id", "rank"),
    )
