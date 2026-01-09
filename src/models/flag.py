import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class FlagType(str, enum.Enum):
    USER = "user"
    ROOT = "root"


class Flag(Base):
    __tablename__ = "flags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    tick_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ticks.id"), nullable=False)
    
    flag_type: Mapped[FlagType] = mapped_column(Enum(FlagType, native_enum=False), default=FlagType.USER)
    flag_value: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    
    valid_until: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    is_stolen: Mapped[bool] = mapped_column(Boolean, default=False)
    stolen_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    game: Mapped["Game"] = relationship(back_populates="flags")
    tick: Mapped["Tick"] = relationship(back_populates="flags")
    submissions: Mapped[list["FlagSubmission"]] = relationship(back_populates="flag")
    
    __table_args__ = (
        Index("ix_flags_game_team_tick_type", "game_id", "team_id", "tick_id", "flag_type", unique=True),
    )


from src.models.game import Game
from src.models.tick import Tick
from src.models.submission import FlagSubmission
