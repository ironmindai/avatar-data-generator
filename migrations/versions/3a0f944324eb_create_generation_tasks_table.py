"""create_generation_tasks_table

Revision ID: 3a0f944324eb
Revises: d8cfd3cb4083
Create Date: 2026-01-30 12:02:12.748294

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a0f944324eb'
down_revision = 'd8cfd3cb4083'
branch_labels = None
depends_on = None


def upgrade():
    # Create generation_tasks table
    op.create_table(
        'generation_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=12), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('persona_description', sa.Text(), nullable=False),
        sa.Column('bio_language', sa.String(length=100), nullable=False),
        sa.Column('number_to_generate', sa.Integer(), nullable=False),
        sa.Column('images_per_persona', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('error_log', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_generation_tasks_user_id'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id', name='uq_generation_tasks_task_id')
    )

    # Create indexes
    op.create_index(
        'ix_generation_tasks_task_id',
        'generation_tasks',
        ['task_id'],
        unique=True
    )
    op.create_index(
        'ix_generation_tasks_user_id',
        'generation_tasks',
        ['user_id'],
        unique=False
    )
    op.create_index(
        'ix_generation_tasks_status',
        'generation_tasks',
        ['status'],
        unique=False
    )


def downgrade():
    # Drop indexes
    op.drop_index('ix_generation_tasks_status', table_name='generation_tasks')
    op.drop_index('ix_generation_tasks_user_id', table_name='generation_tasks')
    op.drop_index('ix_generation_tasks_task_id', table_name='generation_tasks')

    # Drop table
    op.drop_table('generation_tasks')
