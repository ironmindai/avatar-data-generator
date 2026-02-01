"""add_randomize_image_style_config

Revision ID: d8982580d2a4
Revises: 70c50b9233b6
Create Date: 2026-02-01 07:24:32.702688

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8982580d2a4'
down_revision = '70c50b9233b6'
branch_labels = None
depends_on = None


def upgrade():
    # Insert the new randomize_image_style config setting with default value False
    op.execute("""
        INSERT INTO config (key, value, created_at, updated_at)
        VALUES ('randomize_image_style', FALSE, NOW(), NOW())
    """)


def downgrade():
    # Remove the randomize_image_style config setting
    op.execute("""
        DELETE FROM config WHERE key = 'randomize_image_style'
    """)
