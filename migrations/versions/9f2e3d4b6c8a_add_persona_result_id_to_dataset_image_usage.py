"""add_persona_result_id_to_dataset_image_usage

Revision ID: 9f2e3d4b6c8a
Revises: 1a0315a32006
Create Date: 2026-03-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f2e3d4b6c8a'
down_revision = '1a0315a32006'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add persona_result_id column (nullable initially for existing data)
    op.add_column('dataset_image_usage',
        sa.Column('persona_result_id', sa.Integer(), nullable=True)
    )

    # 2. Add foreign key constraint
    op.create_foreign_key(
        'fk_dataset_image_usage_persona_result_id',
        'dataset_image_usage', 'generation_results',
        ['persona_result_id'], ['id'],
        ondelete='CASCADE'
    )

    # 3. Create index for persona_result_id
    op.create_index('ix_dataset_image_usage_persona_result_id', 'dataset_image_usage', ['persona_result_id'])

    # 4. Drop old unique constraint
    op.drop_constraint('uq_dataset_image_usage_image_task', 'dataset_image_usage', type_='unique')

    # 5. Create new unique constraint to include persona_result_id
    op.create_unique_constraint(
        'uq_dataset_image_task_persona',
        'dataset_image_usage',
        ['dataset_image_id', 'task_id', 'persona_result_id']
    )


def downgrade():
    # Drop new unique constraint
    op.drop_constraint('uq_dataset_image_task_persona', 'dataset_image_usage', type_='unique')

    # Recreate old unique constraint
    op.create_unique_constraint(
        'uq_dataset_image_usage_image_task',
        'dataset_image_usage',
        ['dataset_image_id', 'task_id']
    )

    # Drop index
    op.drop_index('ix_dataset_image_usage_persona_result_id', table_name='dataset_image_usage')

    # Drop foreign key constraint
    op.drop_constraint('fk_dataset_image_usage_persona_result_id', 'dataset_image_usage', type_='foreignkey')

    # Drop column
    op.drop_column('dataset_image_usage', 'persona_result_id')
