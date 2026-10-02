"""initial schema

Revision ID: 001
Revises: 
Create Date: 2024-05-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create Enum Type
    op.execute("CREATE TYPE analysisstatus AS ENUM ('PENDING', 'RUNNING', 'DONE', 'FAILED')")

    op.create_table('repositories',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_repositories_url'), 'repositories', ['url'], unique=True)
    
    op.create_table('analyses',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('repo_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('status', sa.Enum('PENDING', 'RUNNING', 'DONE', 'FAILED', name='analysisstatus'), nullable=True),
    sa.Column('triggered_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['repo_id'], ['repositories.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('agent_logs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('agent_name', sa.String(), nullable=True),
    sa.Column('input_summary', sa.Text(), nullable=True),
    sa.Column('output_summary', sa.Text(), nullable=True),
    sa.Column('tokens_used', sa.Integer(), nullable=True),
    sa.Column('duration_ms', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    op.create_table('reports',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('analysis_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('markdown_content', sa.Text(), nullable=True),
    sa.Column('severity_counts', sa.JSON(), nullable=True),
    sa.Column('faithfulness_score', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['analysis_id'], ['analyses.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('analysis_id')
    )


def downgrade() -> None:
    op.drop_table('reports')
    op.drop_table('agent_logs')
    op.drop_table('analyses')
    op.drop_index(op.f('ix_repositories_url'), table_name='repositories')
    op.drop_table('repositories')
    op.execute("DROP TYPE analysisstatus")
