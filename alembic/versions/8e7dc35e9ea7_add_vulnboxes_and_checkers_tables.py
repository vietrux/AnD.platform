"""Add vulnboxes and checkers tables

Revision ID: 8e7dc35e9ea7
Revises: b1c18323c759
Create Date: 2025-12-31 00:27:44.577798

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8e7dc35e9ea7'
down_revision: Union[str, None] = 'b1c18323c759'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'vulnboxes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('path', sa.String(length=500), nullable=False),
        sa.Column('docker_image', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    op.create_table(
        'checkers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('module_name', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    op.add_column('games', sa.Column('vulnbox_id', sa.UUID(), nullable=True))
    op.add_column('games', sa.Column('checker_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_games_vulnbox_id', 'games', 'vulnboxes', ['vulnbox_id'], ['id'])
    op.create_foreign_key('fk_games_checker_id', 'games', 'checkers', ['checker_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_games_checker_id', 'games', type_='foreignkey')
    op.drop_constraint('fk_games_vulnbox_id', 'games', type_='foreignkey')
    op.drop_column('games', 'checker_id')
    op.drop_column('games', 'vulnbox_id')
    op.drop_table('checkers')
    op.drop_table('vulnboxes')
