"""remove_base_image_size_from_generation_results

Revision ID: 42eba0ec3095
Revises: 312faec904ca
Create Date: 2026-02-25 16:26:48.669898

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '42eba0ec3095'
down_revision = '312faec904ca'
branch_labels = None
depends_on = None


def upgrade():
    # Remove base_image_size column from generation_results table
    # This field is no longer needed as dimensions are randomized in code
    # Check if column exists before dropping (for databases that never had this column)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('generation_results')]
    if 'base_image_size' in columns:
        op.drop_column('generation_results', 'base_image_size')


def downgrade():
    # Re-add base_image_size column if rollback is needed
    op.add_column('generation_results', sa.Column('base_image_size', sa.String(length=20), nullable=True))
