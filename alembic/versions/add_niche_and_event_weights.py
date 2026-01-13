"""Add niche field and event weights

Revision ID: add_niche_weights_20260112
Revises: add_psychotype_field
Create Date: 2026-01-12 02:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_niche_weights_20260112'
down_revision = 'add_psychotype_field'
branch_labels = None
depends_on = None


def upgrade():
    """
    Добавляет поле niche в таблицы creatives и pattern_performance.

    Ниши:
    - EDTECH: EdTech, языковые курсы, онлайн обучение
    - HEALTH: Health & Fitness, workout, nutrition
    """
    # 1. Добавить поле niche в creatives
    op.add_column('creatives', sa.Column('niche', sa.String(50), nullable=True))

    # 2. Добавить поле niche в pattern_performance
    op.add_column('pattern_performance', sa.Column('niche', sa.String(50), nullable=True))

    # 3. Создать индексы для быстрого поиска по niche
    op.create_index('ix_creatives_niche', 'creatives', ['niche'])
    op.create_index('ix_pattern_performance_niche', 'pattern_performance', ['niche'])

    # 4. Мигрировать существующие данные: product_category → niche
    # language_learning, education, edtech → EDTECH
    # fitness, health → HEALTH
    op.execute("""
        UPDATE creatives
        SET niche = CASE
            WHEN product_category IN ('language_learning', 'education', 'edtech') THEN 'EDTECH'
            WHEN product_category IN ('fitness', 'health', 'workout', 'nutrition') THEN 'HEALTH'
            ELSE 'EDTECH'
        END
        WHERE niche IS NULL
    """)

    op.execute("""
        UPDATE pattern_performance
        SET niche = CASE
            WHEN product_category IN ('language_learning', 'education', 'edtech') THEN 'EDTECH'
            WHEN product_category IN ('fitness', 'health', 'workout', 'nutrition') THEN 'HEALTH'
            ELSE 'EDTECH'
        END
        WHERE niche IS NULL
    """)

    # 5. Сделать niche NOT NULL после миграции
    op.alter_column('creatives', 'niche', nullable=False)
    op.alter_column('pattern_performance', 'niche', nullable=False)

    print("✅ Migration completed: niche field added to creatives and pattern_performance")


def downgrade():
    """
    Откатить миграцию (удалить поле niche).
    """
    # Удалить индексы
    op.drop_index('ix_pattern_performance_niche', table_name='pattern_performance')
    op.drop_index('ix_creatives_niche', table_name='creatives')

    # Удалить столбцы
    op.drop_column('pattern_performance', 'niche')
    op.drop_column('creatives', 'niche')

    print("✅ Downgrade completed: niche field removed")
