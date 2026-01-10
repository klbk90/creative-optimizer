"""add psychotype field to creatives and pattern_performance

Revision ID: add_psychotype_field
Revises: add_market_ingestion_fields
Create Date: 2026-01-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_psychotype_field'
down_revision = 'add_market_ingestion_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add psychotype column to creatives table
    op.add_column('creatives', sa.Column('psychotype', sa.String(length=100), nullable=True))
    op.create_index('ix_creatives_psychotype', 'creatives', ['psychotype'], unique=False)

    # Add psychotype column to pattern_performance table
    op.add_column('pattern_performance', sa.Column('psychotype', sa.String(length=100), nullable=True))
    op.create_index('ix_pattern_performance_psychotype', 'pattern_performance', ['psychotype'], unique=False)


def downgrade():
    # Drop indexes and columns in reverse order
    op.drop_index('ix_pattern_performance_psychotype', table_name='pattern_performance')
    op.drop_column('pattern_performance', 'psychotype')

    op.drop_index('ix_creatives_psychotype', table_name='creatives')
    op.drop_column('creatives', 'psychotype')
