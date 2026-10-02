"""add eval metrics

Revision ID: 002
Revises: 001
Create Date: 2026-10-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('reports', sa.Column('avg_finding_relevance', sa.Float(), nullable=True))
    op.add_column('reports', sa.Column('avg_actionability', sa.Float(), nullable=True))

def downgrade() -> None:
    op.drop_column('reports', 'avg_actionability')
    op.drop_column('reports', 'avg_finding_relevance')
