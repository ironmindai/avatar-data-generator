"""add_image_set_ids_and_dataset_image_usage_tracking

Revision ID: 1a0315a32006
Revises: 562b42df8d87
Create Date: 2026-03-10 07:02:30.028029

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '1a0315a32006'
down_revision = '562b42df8d87'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add image_set_ids column to generation_tasks table
    # This stores array of image-set IDs selected by user for this generation task
    # Nullable for backward compatibility with existing tasks
    op.add_column('generation_tasks',
        sa.Column('image_set_ids', postgresql.ARRAY(sa.Integer()), nullable=True)
    )

    # 2. Create dataset_image_usage table for tracking scene image usage
    # This enables prioritizing least-used images and avoiding repetition
    op.create_table('dataset_image_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_image_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('used_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['dataset_image_id'], ['dataset_images.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['generation_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dataset_image_id', 'task_id', name='uq_dataset_image_usage_image_task')
    )

    # 3. Create indexes for efficient lookups
    op.create_index('ix_dataset_image_usage_dataset_image_id', 'dataset_image_usage', ['dataset_image_id'])
    op.create_index('ix_dataset_image_usage_task_id', 'dataset_image_usage', ['task_id'])


def downgrade():
    # Drop indexes first
    op.drop_index('ix_dataset_image_usage_task_id', table_name='dataset_image_usage')
    op.drop_index('ix_dataset_image_usage_dataset_image_id', table_name='dataset_image_usage')

    # Drop dataset_image_usage table
    op.drop_table('dataset_image_usage')

    # Remove image_set_ids column from generation_tasks
    op.drop_column('generation_tasks', 'image_set_ids')
