"""add_crop_white_borders_config

Revision ID: 70c50b9233b6
Revises: d59663db64e2
Create Date: 2026-01-31 15:02:23.451820

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70c50b9233b6'
down_revision = 'd59663db64e2'
branch_labels = None
depends_on = None


def upgrade():
    # Insert the new crop_white_borders config setting with default value False
    op.execute("""
        INSERT INTO config (key, value, created_at, updated_at)
        VALUES ('crop_white_borders', FALSE, NOW(), NOW())
    """)


def downgrade():
    # Remove the crop_white_borders config setting
    op.execute("""
        DELETE FROM config WHERE key = 'crop_white_borders'
    """)
