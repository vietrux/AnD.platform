import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class TickStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ERROR = "error"


class Tick(Base):
    __tablename__ = "ticks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    
    tick_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[TickStatus] = mapped_column(Enum(TickStatus, native_enum=False), default=TickStatus.PENDING)
    
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    flags_placed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    game: Mapped["Game"] = relationship(back_populates="ticks")
    flags: Mapped[list["Flag"]] = relationship(back_populates="tick", cascade="all, delete-orphan")
    service_statuses: Mapped[list["ServiceStatus"]] = relationship(back_populates="tick", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_ticks_game_number", "game_id", "tick_number", unique=True),
    )


from src.models.game import Game
from src.models.flag import Flag
from src.models.service_status import ServiceStatus
