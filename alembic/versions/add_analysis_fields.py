"""Add analysis tracking fields to creatives

Revision ID: add_analysis_001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'add_analysis_001'
down_revision = '001_add_influencer_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to creatives table
    op.add_column('creatives', sa.Column('analysis_status', sa.String(20), server_default='pending'))
    op.add_column('creatives', sa.Column('is_benchmark', sa.Boolean(), server_default='false'))
    op.add_column('creatives', sa.Column('deeply_analyzed', sa.Boolean(), server_default='false'))
    op.add_column('creatives', sa.Column('ai_reasoning', sa.Text(), nullable=True))
    op.add_column('creatives', sa.Column('analysis_cost_cents', sa.Integer(), server_default='0'))
    op.add_column('creatives', sa.Column('analysis_triggered_at', sa.DateTime(), nullable=True))
    op.add_column('creatives', sa.Column('analyzed_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('creatives', 'analyzed_at')
    op.drop_column('creatives', 'analysis_triggered_at')
    op.drop_column('creatives', 'analysis_cost_cents')
    op.drop_column('creatives', 'ai_reasoning')
    op.drop_column('creatives', 'deeply_analyzed')
    op.drop_column('creatives', 'is_benchmark')
    op.drop_column('creatives', 'analysis_status')
