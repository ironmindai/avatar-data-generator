"""add_supplementary_persona_fields_job_education_location_about

Revision ID: 7e69fd85074a
Revises: 8a3b5c7d9e0f
Create Date: 2026-02-05 18:40:45.016668

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e69fd85074a'
down_revision = '8a3b5c7d9e0f'
branch_labels = None
depends_on = None


def upgrade():
    # Add supplementary persona fields to generation_results table
    op.add_column('generation_results', sa.Column('job_title', sa.Text(), nullable=True))
    op.add_column('generation_results', sa.Column('workplace', sa.Text(), nullable=True))
    op.add_column('generation_results', sa.Column('edu_establishment', sa.Text(), nullable=True))
    op.add_column('generation_results', sa.Column('edu_study', sa.Text(), nullable=True))
    op.add_column('generation_results', sa.Column('current_city', sa.String(length=255), nullable=True))
    op.add_column('generation_results', sa.Column('current_state', sa.String(length=255), nullable=True))
    op.add_column('generation_results', sa.Column('prev_city', sa.String(length=255), nullable=True))
    op.add_column('generation_results', sa.Column('prev_state', sa.String(length=255), nullable=True))
    op.add_column('generation_results', sa.Column('about', sa.Text(), nullable=True))


def downgrade():
    # Remove supplementary persona fields from generation_results table
    op.drop_column('generation_results', 'about')
    op.drop_column('generation_results', 'prev_state')
    op.drop_column('generation_results', 'prev_city')
    op.drop_column('generation_results', 'current_state')
    op.drop_column('generation_results', 'current_city')
    op.drop_column('generation_results', 'edu_study')
    op.drop_column('generation_results', 'edu_establishment')
    op.drop_column('generation_results', 'workplace')
    op.drop_column('generation_results', 'job_title')
