"""add_image_ideas_history_to_generation_results

Revision ID: 312faec904ca
Revises: fbc78f685fa2
Create Date: 2026-02-19 12:42:06.746032

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '312faec904ca'
down_revision = 'fbc78f685fa2'
branch_labels = None
depends_on = None


def upgrade():
    """Add image_ideas_history JSONB column to generation_results table."""
    # Add the column as JSONB array (nullable) to store image idea history
    op.add_column('generation_results',
                  sa.Column('image_ideas_history', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade():
    """Remove image_ideas_history column from generation_results table."""
    # Drop the column - WARNING: This will permanently delete all image ideas history data
    op.drop_column('generation_results', 'image_ideas_history')
