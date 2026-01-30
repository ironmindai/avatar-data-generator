"""create generation_results table

Revision ID: 3d677a879bd9
Revises: 3a0f944324eb
Create Date: 2026-01-30 13:07:31.828662

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d677a879bd9'
down_revision = '3a0f944324eb'
branch_labels = None
depends_on = None


def upgrade():
    # Create generation_results table
    op.create_table(
        'generation_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('batch_number', sa.Integer(), nullable=False),
        sa.Column('firstname', sa.String(length=100), nullable=False),
        sa.Column('lastname', sa.String(length=100), nullable=False),
        sa.Column('gender', sa.String(length=10), nullable=False),
        sa.Column('bio_facebook', sa.Text(), nullable=True),
        sa.Column('bio_instagram', sa.Text(), nullable=True),
        sa.Column('bio_x', sa.Text(), nullable=True),
        sa.Column('bio_tiktok', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_generation_results_task_id', 'generation_results', ['task_id'])
    op.create_index('ix_generation_results_batch_number', 'generation_results', ['batch_number'])

    # Create foreign key constraint to generation_tasks table
    op.create_foreign_key(
        'fk_generation_results_task_id',
        'generation_results',
        'generation_tasks',
        ['task_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    # Drop foreign key first
    op.drop_constraint('fk_generation_results_task_id', 'generation_results', type_='foreignkey')

    # Drop indexes
    op.drop_index('ix_generation_results_batch_number', 'generation_results')
    op.drop_index('ix_generation_results_task_id', 'generation_results')

    # Drop table
    op.drop_table('generation_results')
