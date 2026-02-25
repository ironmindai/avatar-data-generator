"""add_show_base_images_config

Revision ID: a5b7c9d1e3f5
Revises: 42eba0ec3095
Create Date: 2026-02-25 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5b7c9d1e3f5'
down_revision = '42eba0ec3095'
branch_labels = None
depends_on = None


def upgrade():
    # Insert the new show_base_images config setting with default value True
    # This controls whether base images are displayed in the dataset detail view
    op.execute("""
        INSERT INTO config (key, value, created_at, updated_at)
        VALUES ('show_base_images', TRUE, NOW(), NOW())
        ON CONFLICT (key) DO NOTHING
    """)


def downgrade():
    # Remove the show_base_images config setting
    op.execute("""
        DELETE FROM config WHERE key = 'show_base_images'
    """)
