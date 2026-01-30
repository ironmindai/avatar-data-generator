"""add_s3_image_url_fields_to_generation_results

Revision ID: 36b6aa503da9
Revises: 3d677a879bd9
Create Date: 2026-01-30 15:01:07.254765

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '36b6aa503da9'
down_revision = '3d677a879bd9'
branch_labels = None
depends_on = None


def upgrade():
    # Add S3 image URL fields to generation_results table
    # These fields store public URLs for generated avatar images
    # All fields are nullable as images are generated after persona data
    op.add_column('generation_results', sa.Column('base_image_url', sa.Text(), nullable=True))
    op.add_column('generation_results', sa.Column('image_1_url', sa.Text(), nullable=True))
    op.add_column('generation_results', sa.Column('image_2_url', sa.Text(), nullable=True))
    op.add_column('generation_results', sa.Column('image_3_url', sa.Text(), nullable=True))
    op.add_column('generation_results', sa.Column('image_4_url', sa.Text(), nullable=True))


def downgrade():
    # Remove S3 image URL fields from generation_results table
    # WARNING: This will permanently delete all stored image URLs
    op.drop_column('generation_results', 'image_4_url')
    op.drop_column('generation_results', 'image_3_url')
    op.drop_column('generation_results', 'image_2_url')
    op.drop_column('generation_results', 'image_1_url')
    op.drop_column('generation_results', 'base_image_url')
