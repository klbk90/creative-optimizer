"""Add influencer and EdTech-specific fields

Revision ID: 001_add_influencer_fields
Revises:
Create Date: 2026-01-01 21:43:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_add_influencer_fields'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add fields for:
    1. Influencer tracking in TrafficSource
    2. EdTech pain points in Creative and PatternPerformance
    3. RudderStack external_id tracking
    4. Pattern hash for quick lookup
    """

    # Add fields to traffic_sources table
    op.add_column('traffic_sources', sa.Column('creative_id', sa.UUID(), nullable=True))
    op.add_column('traffic_sources', sa.Column('influencer_handle', sa.String(100), nullable=True))
    op.add_column('traffic_sources', sa.Column('influencer_email', sa.String(255), nullable=True))
    op.add_column('traffic_sources', sa.Column('influencer_followers', sa.Integer(), nullable=True))
    op.add_column('traffic_sources', sa.Column('influencer_engagement_rate', sa.Integer(), nullable=True))
    op.add_column('traffic_sources', sa.Column('influencer_status', sa.String(50), nullable=True))
    op.add_column('traffic_sources', sa.Column('external_id', sa.String(255), nullable=True))

    # Create foreign key for creative_id
    op.create_foreign_key(
        'fk_traffic_sources_creative_id',
        'traffic_sources',
        'creatives',
        ['creative_id'],
        ['id']
    )

    # Create indexes for traffic_sources
    op.create_index('ix_traffic_sources_creative_id', 'traffic_sources', ['creative_id'])
    op.create_index('ix_traffic_sources_influencer_handle', 'traffic_sources', ['influencer_handle'])

    # Add fields to conversions table
    op.add_column('conversions', sa.Column('external_id', sa.String(255), nullable=True))

    # Add fields to creatives table
    op.add_column('creatives', sa.Column('target_audience_pain', sa.String(100), nullable=True))

    # Add fields to pattern_performance table
    op.add_column('pattern_performance', sa.Column('pattern_hash', sa.String(255), nullable=True))
    op.add_column('pattern_performance', sa.Column('target_audience_pain', sa.String(100), nullable=True))

    # Create indexes for pattern_performance
    op.create_index('ix_pattern_performance_pattern_hash', 'pattern_performance', ['pattern_hash'])
    op.create_index('ix_pattern_performance_target_audience_pain', 'pattern_performance', ['target_audience_pain'])

    print("✅ Migration 001: Added influencer and EdTech fields")


def downgrade() -> None:
    """
    Remove added fields
    """

    # Drop indexes
    op.drop_index('ix_pattern_performance_target_audience_pain', 'pattern_performance')
    op.drop_index('ix_pattern_performance_pattern_hash', 'pattern_performance')
    op.drop_index('ix_traffic_sources_influencer_handle', 'traffic_sources')
    op.drop_index('ix_traffic_sources_creative_id', 'traffic_sources')

    # Drop foreign key
    op.drop_constraint('fk_traffic_sources_creative_id', 'traffic_sources', type_='foreignkey')

    # Drop columns from pattern_performance
    op.drop_column('pattern_performance', 'target_audience_pain')
    op.drop_column('pattern_performance', 'pattern_hash')

    # Drop columns from creatives
    op.drop_column('creatives', 'target_audience_pain')

    # Drop columns from conversions
    op.drop_column('conversions', 'external_id')

    # Drop columns from traffic_sources
    op.drop_column('traffic_sources', 'external_id')
    op.drop_column('traffic_sources', 'influencer_status')
    op.drop_column('traffic_sources', 'influencer_engagement_rate')
    op.drop_column('traffic_sources', 'influencer_followers')
    op.drop_column('traffic_sources', 'influencer_email')
    op.drop_column('traffic_sources', 'influencer_handle')
    op.drop_column('traffic_sources', 'creative_id')

    print("✅ Migration 001: Rolled back influencer and EdTech fields")
