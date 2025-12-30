import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Text, Integer, DateTime, Enum, ForeignKey, Boolean, Float, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from src.core.database import Base


class GameStatus(str, enum.Enum):
    DRAFT = "draft"
    DEPLOYING = "deploying"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"


class Game(Base):
    __tablename__ = "games"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    vulnbox_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vulnboxes.id"), nullable=True
    )
    checker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checkers.id"), nullable=True
    )
    
    vulnbox_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    checker_module: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    status: Mapped[GameStatus] = mapped_column(
        Enum(GameStatus), default=GameStatus.DRAFT, nullable=False
    )
    
    tick_duration_seconds: Mapped[int] = mapped_column(Integer, default=60)
    current_tick: Mapped[int] = mapped_column(Integer, default=0)
    
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    vulnbox: Mapped["Vulnbox | None"] = relationship("Vulnbox", foreign_keys=[vulnbox_id])
    checker: Mapped["Checker | None"] = relationship("Checker", foreign_keys=[checker_id])
    game_teams: Mapped[list["GameTeam"]] = relationship(back_populates="game", cascade="all, delete-orphan")
    ticks: Mapped[list["Tick"]] = relationship(back_populates="game", cascade="all, delete-orphan")
    flags: Mapped[list["Flag"]] = relationship(back_populates="game", cascade="all, delete-orphan")




class GameTeam(Base):
    __tablename__ = "game_teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    team_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    container_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    container_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    ssh_username: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ssh_password: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ssh_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    game: Mapped["Game"] = relationship(back_populates="game_teams")
    
    __table_args__ = (
        Index("ix_game_teams_game_team", "game_id", "team_id", unique=True),
    )
