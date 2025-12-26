"""Initial migration

Revision ID: b1c18323c759
Revises: 
Create Date: 2025-12-26 01:08:47.377972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b1c18323c759'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('games',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('vulnbox_path', sa.String(length=500), nullable=True),
        sa.Column('checker_module', sa.String(length=200), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'DEPLOYING', 'RUNNING', 'PAUSED', 'FINISHED', name='gamestatus'), nullable=False),
        sa.Column('tick_duration_seconds', sa.Integer(), nullable=False),
        sa.Column('current_tick', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    op.create_table('game_teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('team_id', sa.String(length=100), nullable=False),
        sa.Column('container_name', sa.String(length=200), nullable=True),
        sa.Column('container_ip', sa.String(length=50), nullable=True),
        sa.Column('ssh_username', sa.String(length=50), nullable=True),
        sa.Column('ssh_password', sa.String(length=100), nullable=True),
        sa.Column('ssh_port', sa.Integer(), nullable=True),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index('ix_game_teams_game_team', 'game_teams', ['game_id', 'team_id'], unique=True)
    op.create_index('ix_game_teams_team_id', 'game_teams', ['team_id'], unique=False)
    op.create_index('ix_game_teams_token', 'game_teams', ['token'], unique=False)
    
    op.create_table('ticks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tick_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'ACTIVE', 'COMPLETED', 'ERROR', name='tickstatus'), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('flags_placed', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ticks_game_number', 'ticks', ['game_id', 'tick_number'], unique=True)
    
    op.create_table('flags',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('team_id', sa.String(length=100), nullable=False),
        sa.Column('tick_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('flag_type', sa.Enum('USER', 'ROOT', name='flagtype'), nullable=False),
        sa.Column('flag_value', sa.String(length=128), nullable=False),
        sa.Column('valid_until', sa.DateTime(), nullable=False),
        sa.Column('is_stolen', sa.Boolean(), nullable=False),
        sa.Column('stolen_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id']),
        sa.ForeignKeyConstraint(['tick_id'], ['ticks.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('flag_value')
    )
    op.create_index('ix_flags_team_id', 'flags', ['team_id'], unique=False)
    op.create_index('ix_flags_flag_value', 'flags', ['flag_value'], unique=False)
    op.create_index('ix_flags_game_team_tick_type', 'flags', ['game_id', 'team_id', 'tick_id', 'flag_type'], unique=True)
    
    op.create_table('flag_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attacker_team_id', sa.String(length=100), nullable=False),
        sa.Column('flag_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('submitted_flag', sa.String(length=128), nullable=False),
        sa.Column('status', sa.Enum('ACCEPTED', 'REJECTED', 'DUPLICATE', 'EXPIRED', 'OWN_FLAG', 'INVALID', name='submissionstatus'), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['flag_id'], ['flags.id']),
        sa.ForeignKeyConstraint(['game_id'], ['games.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_submissions_attacker_team_id', 'flag_submissions', ['attacker_team_id'], unique=False)
    op.create_index('ix_submissions_submitted_flag', 'flag_submissions', ['submitted_flag'], unique=False)
    op.create_index('ix_submissions_submitted_at', 'flag_submissions', ['submitted_at'], unique=False)
    op.create_index('ix_submissions_game_attacker', 'flag_submissions', ['game_id', 'attacker_team_id'], unique=False)
    
    op.create_table('service_statuses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('team_id', sa.String(length=100), nullable=False),
        sa.Column('tick_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.Enum('UP', 'DOWN', 'ERROR', name='checkstatus'), nullable=False),
        sa.Column('sla_percentage', sa.Float(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('check_duration_ms', sa.Integer(), nullable=True),
        sa.Column('checked_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id']),
        sa.ForeignKeyConstraint(['tick_id'], ['ticks.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_service_status_team_id', 'service_statuses', ['team_id'], unique=False)
    op.create_index('ix_service_status_game_team_tick', 'service_statuses', ['game_id', 'team_id', 'tick_id'], unique=True)
    
    op.create_table('scoreboard',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('game_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('team_id', sa.String(length=100), nullable=False),
        sa.Column('attack_points', sa.Integer(), nullable=False),
        sa.Column('defense_points', sa.Integer(), nullable=False),
        sa.Column('sla_points', sa.Integer(), nullable=False),
        sa.Column('total_points', sa.Integer(), nullable=False),
        sa.Column('rank', sa.Integer(), nullable=False),
        sa.Column('flags_captured', sa.Integer(), nullable=False),
        sa.Column('flags_lost', sa.Integer(), nullable=False),
        sa.Column('last_updated', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['game_id'], ['games.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_scoreboard_team_id', 'scoreboard', ['team_id'], unique=False)
    op.create_index('ix_scoreboard_total_points', 'scoreboard', ['total_points'], unique=False)
    op.create_index('ix_scoreboard_game_team', 'scoreboard', ['game_id', 'team_id'], unique=True)
    op.create_index('ix_scoreboard_game_rank', 'scoreboard', ['game_id', 'rank'], unique=False)


def downgrade() -> None:
    op.drop_table('scoreboard')
    op.drop_table('service_statuses')
    op.drop_table('flag_submissions')
    op.drop_table('flags')
    op.drop_table('ticks')
    op.drop_table('game_teams')
    op.drop_table('games')
    
    op.execute("DROP TYPE IF EXISTS gamestatus")
    op.execute("DROP TYPE IF EXISTS tickstatus")
    op.execute("DROP TYPE IF EXISTS flagtype")
    op.execute("DROP TYPE IF EXISTS submissionstatus")
    op.execute("DROP TYPE IF EXISTS checkstatus")
