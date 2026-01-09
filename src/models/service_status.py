import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Enum, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class CheckStatus(str, enum.Enum):
    UP = "up"
    DOWN = "down"
    ERROR = "error"


class ServiceStatus(Base):
    __tablename__ = "service_statuses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tick_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ticks.id"), nullable=False)
    
    status: Mapped[CheckStatus] = mapped_column(Enum(CheckStatus, native_enum=False), default=CheckStatus.UP)
    sla_percentage: Mapped[float] = mapped_column(Float, default=100.0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    check_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tick: Mapped["Tick"] = relationship(back_populates="service_statuses")
    
    __table_args__ = (
        Index("ix_service_status_game_team_tick", "game_id", "team_id", "tick_id", unique=True),
    )


from src.models.tick import Tick
