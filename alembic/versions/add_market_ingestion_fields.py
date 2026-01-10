"""Add market ingestion fields to PatternPerformance and Creative

Revision ID: market_ingestion_001
Revises: add_analysis_fields
Create Date: 2026-01-06

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'market_ingestion_001'
down_revision = 'add_analysis_001'  # Previous migration
branch_labels = None
depends_on = None


def upgrade():
    """
    Add market ingestion fields to PatternPerformance and Creative.

    PatternPerformance:
    - source: 'benchmark' or 'client'
    - weight: float (benchmark=2.0, client=1.0)
    - market_longevity_days: int
    - bayesian_alpha: float
    - bayesian_beta: float

    Creative:
    - is_public: boolean (for security)
    """

    # Add PatternPerformance fields
    op.add_column('pattern_performance', sa.Column('source', sa.String(50), server_default='client'))
    op.add_column('pattern_performance', sa.Column('weight', sa.Float(), server_default='1.0'))
    op.add_column('pattern_performance', sa.Column('market_longevity_days', sa.Integer(), nullable=True))
    op.add_column('pattern_performance', sa.Column('bayesian_alpha', sa.Float(), server_default='1.0'))
    op.add_column('pattern_performance', sa.Column('bayesian_beta', sa.Float(), server_default='1.0'))

    # Add Creative field
    op.add_column('creatives', sa.Column('is_public', sa.Boolean(), server_default='false'))

    # Create indexes for performance
    op.create_index('idx_pattern_performance_source', 'pattern_performance', ['source'])
    op.create_index('idx_creatives_is_public', 'creatives', ['is_public'])

    # Update existing benchmarks to have proper weight
    op.execute("""
        UPDATE pattern_performance
        SET source = 'benchmark', weight = 2.0
        WHERE user_id = '00000000-0000-0000-0000-000000000001'
    """)

    # Update existing benchmark creatives to be public
    op.execute("""
        UPDATE creatives
        SET is_public = true
        WHERE is_benchmark = true
    """)


def downgrade():
    """Remove market ingestion fields."""

    # Drop indexes
    op.drop_index('idx_pattern_performance_source', 'pattern_performance')
    op.drop_index('idx_creatives_is_public', 'creatives')

    # Drop columns
    op.drop_column('pattern_performance', 'bayesian_beta')
    op.drop_column('pattern_performance', 'bayesian_alpha')
    op.drop_column('pattern_performance', 'market_longevity_days')
    op.drop_column('pattern_performance', 'weight')
    op.drop_column('pattern_performance', 'source')
    op.drop_column('creatives', 'is_public')
