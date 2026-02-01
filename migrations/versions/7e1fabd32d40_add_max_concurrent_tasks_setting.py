"""add_max_concurrent_tasks_setting

Revision ID: 7e1fabd32d40
Revises: d8982580d2a4
Create Date: 2026-02-01 08:18:07.058684

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e1fabd32d40'
down_revision = 'd8982580d2a4'
branch_labels = None
depends_on = None


def upgrade():
    # Insert the new max_concurrent_tasks setting with default value '1'
    # This setting controls how many avatar generation tasks can process simultaneously
    # Value of '1' means tasks process sequentially (one at a time)
    op.execute("""
        INSERT INTO settings (key, value, created_at, updated_at)
        VALUES ('max_concurrent_tasks', '1', NOW(), NOW())
    """)


def downgrade():
    # Remove the max_concurrent_tasks setting
    op.execute("""
        DELETE FROM settings WHERE key = 'max_concurrent_tasks'
    """)
