"""add_ethnicity_and_age_to_generation_results

Revision ID: fbc78f685fa2
Revises: 7e69fd85074a
Create Date: 2026-02-19 06:41:56.592246

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fbc78f685fa2'
down_revision = '7e69fd85074a'
branch_labels = None
depends_on = None


def upgrade():
    # Add ethnicity column - String(100), nullable
    # Comes from root level of Flowise response (e.g., "ethnicity": "White")
    op.add_column('generation_results', sa.Column('ethnicity', sa.String(length=100), nullable=True))

    # Add age column - Integer, nullable
    # Comes from inside bios JSON object (e.g., "age": 23)
    op.add_column('generation_results', sa.Column('age', sa.Integer(), nullable=True))


def downgrade():
    # Remove age column
    op.drop_column('generation_results', 'age')

    # Remove ethnicity column
    op.drop_column('generation_results', 'ethnicity')
