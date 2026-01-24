"""Add influencers table for scraper pipeline

Revision ID: add_influencers_20260124
Revises: add_niche_weights_20260112
Create Date: 2026-01-24

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_influencers_20260124'
down_revision = 'add_niche_weights_20260112'
branch_labels = None
depends_on = None


def upgrade():
    """
    Создает таблицу influencers для хранения данных инфлюенсеров.

    Пайплайн:
    1. Скрапер (Apify) собирает по хэштегам → status=new
    2. RocketReach пробивает email → status=email_found
    3. Outreach → status=contacted/responded/agreed/posted
    """
    op.create_table(
        'influencers',
        # Primary key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),

        # Basic info (from scraper)
        sa.Column('handle', sa.String(100), nullable=False),
        sa.Column('name', sa.String(200), nullable=True),
        sa.Column('bio', sa.Text, nullable=True),
        sa.Column('platform', sa.String(50), nullable=False),

        # Niche (key field for filtering)
        sa.Column('niche', sa.String(100), nullable=False),

        # Metrics
        sa.Column('followers', sa.Integer, nullable=False, default=0),
        sa.Column('following', sa.Integer, nullable=True),
        sa.Column('engagement_rate', sa.Integer, nullable=True),  # ER * 10000
        sa.Column('avg_views', sa.Integer, nullable=True),
        sa.Column('total_likes', sa.BigInteger, nullable=True),
        sa.Column('total_videos', sa.Integer, nullable=True),

        # Email (from RocketReach)
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('email_source', sa.String(50), nullable=True),
        sa.Column('email_verified', sa.Boolean, default=False),

        # Funnel status
        sa.Column('status', sa.String(50), nullable=False, default='new'),

        # Source data
        sa.Column('source_keyword', sa.String(200), nullable=True),
        sa.Column('source_hashtag', sa.String(200), nullable=True),
        sa.Column('scraped_from', sa.String(50), default='apify'),

        # Contact tracking
        sa.Column('contacted_at', sa.DateTime, nullable=True),
        sa.Column('responded_at', sa.DateTime, nullable=True),
        sa.Column('agreed_at', sa.DateTime, nullable=True),
        sa.Column('posted_at', sa.DateTime, nullable=True),

        # Campaign link
        sa.Column('traffic_source_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('traffic_sources.id'), nullable=True),
        sa.Column('utm_id', sa.String(100), nullable=True),

        # Extra
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('extra_data', postgresql.JSON, default={}),

        # Timestamps
        sa.Column('scraped_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=True),
    )

    # Create indexes
    op.create_index('ix_influencers_user_id', 'influencers', ['user_id'])
    op.create_index('ix_influencers_handle', 'influencers', ['handle'])
    op.create_index('ix_influencers_platform', 'influencers', ['platform'])
    op.create_index('ix_influencers_niche', 'influencers', ['niche'])
    op.create_index('ix_influencers_status', 'influencers', ['status'])
    op.create_index('ix_influencers_email', 'influencers', ['email'])
    op.create_index('ix_influencers_utm_id', 'influencers', ['utm_id'])
    op.create_index('ix_influencers_created_at', 'influencers', ['created_at'])
    op.create_index('ix_influencers_followers', 'influencers', ['followers'])

    # Composite indexes
    op.create_index('idx_influencer_user_platform_handle', 'influencers', ['user_id', 'platform', 'handle'], unique=True)
    op.create_index('idx_influencer_niche_status', 'influencers', ['niche', 'status'])

    print("✅ Migration completed: influencers table created")


def downgrade():
    """
    Drop influencers table.
    """
    # Drop indexes first
    op.drop_index('idx_influencer_niche_status', table_name='influencers')
    op.drop_index('idx_influencer_user_platform_handle', table_name='influencers')
    op.drop_index('ix_influencers_followers', table_name='influencers')
    op.drop_index('ix_influencers_created_at', table_name='influencers')
    op.drop_index('ix_influencers_utm_id', table_name='influencers')
    op.drop_index('ix_influencers_email', table_name='influencers')
    op.drop_index('ix_influencers_status', table_name='influencers')
    op.drop_index('ix_influencers_niche', table_name='influencers')
    op.drop_index('ix_influencers_platform', table_name='influencers')
    op.drop_index('ix_influencers_handle', table_name='influencers')
    op.drop_index('ix_influencers_user_id', table_name='influencers')

    # Drop table
    op.drop_table('influencers')

    print("✅ Downgrade completed: influencers table dropped")
