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
        UUID(as_uuid=True), ForeignKey("vulnboxes.id", ondelete="SET NULL"), nullable=True
    )
    checker_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("checkers.id", ondelete="SET NULL"), nullable=True
    )
    
    vulnbox_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    checker_module: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    status: Mapped[GameStatus] = mapped_column(
        Enum(GameStatus, native_enum=False), default=GameStatus.DRAFT, nullable=False
    )
    
    tick_duration_seconds: Mapped[int] = mapped_column(Integer, default=60)
    max_ticks: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    current_tick: Mapped[int] = mapped_column(Integer, default=0)
    
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Pause tracking for proper tick calculation
    paused_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    total_paused_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    vulnbox: Mapped["Vulnbox | None"] = relationship("Vulnbox", foreign_keys=[vulnbox_id])
    checker: Mapped["Checker | None"] = relationship("Checker", foreign_keys=[checker_id])
    game_teams: Mapped[list["GameTeam"]] = relationship(back_populates="game", cascade="all, delete-orphan")
    ticks: Mapped[list["Tick"]] = relationship(back_populates="game", cascade="all, delete-orphan")
    flags: Mapped[list["Flag"]] = relationship(back_populates="game", cascade="all, delete-orphan")
    scoreboard_entries: Mapped[list["Scoreboard"]] = relationship(back_populates="game", cascade="all, delete-orphan")




class GameTeam(Base):
    __tablename__ = "game_teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    team_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True, index=True)
    
    container_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    container_ip: Mapped[str | None] = mapped_column(String(50), nullable=True)
    
    ssh_username: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ssh_password: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ssh_port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    game: Mapped["Game"] = relationship(back_populates="game_teams")
    
    __table_args__ = (
        Index("ix_game_teams_game_team", "game_id", "team_id", unique=True),
    )


class GameVulnbox(Base):
    """Junction table for many-to-many relationship between Game and Vulnbox.
    Allows a game to have multiple vulnboxes (services)."""
    __tablename__ = "game_vulnboxes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    game_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    vulnbox_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vulnboxes.id", ondelete="CASCADE"), nullable=False)
    
    # Optional: override paths per game if needed
    vulnbox_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    docker_image: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("ix_game_vulnboxes_game_vulnbox", "game_id", "vulnbox_id", unique=True),
    )

