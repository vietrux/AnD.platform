import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class SubmissionStatus(str, enum.Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    EXPIRED = "expired"
    OWN_FLAG = "own_flag"
    INVALID = "invalid"


class FlagSubmission(Base):
    __tablename__ = "flag_submissions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    attacker_team_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    flag_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("flags.id"), nullable=True)
    
    submitted_flag: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus, native_enum=False), nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0)
    
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    flag: Mapped["Flag | None"] = relationship(back_populates="submissions")
    
    __table_args__ = (
        Index("ix_submissions_game_attacker", "game_id", "attacker_team_id"),
    )


from src.models.flag import Flag
