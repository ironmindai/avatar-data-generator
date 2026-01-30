"""convert_image_urls_to_jsonb_array

Revision ID: 30c18b6939ce
Revises: 36b6aa503da9
Create Date: 2026-01-30 15:24:25.196489

BREAKING CHANGE: Converts individual image_1_url through image_4_url columns
to a JSONB array column 'images' for better flexibility and scalability.

This migration:
1. Creates new 'images' JSONB column
2. Migrates existing data from image_1_url through image_4_url to the JSONB array
3. Drops the old individual image URL columns

Downgrade:
1. Recreates the 4 individual image URL columns
2. Migrates data back from JSONB array to individual columns
3. Drops the 'images' column

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import json


# revision identifiers, used by Alembic.
revision = '30c18b6939ce'
down_revision = '36b6aa503da9'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add new JSONB column for images array
    op.add_column('generation_results', sa.Column('images', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # Step 2: Migrate existing data from individual columns to JSONB array
    # Get database connection
    connection = op.get_bind()

    # SQL to migrate data: create JSON array from non-null image URLs
    # This will build an array like: ["url1", "url2", "url3", "url4"]
    # Only includes non-null URLs
    connection.execute(sa.text("""
        UPDATE generation_results
        SET images = (
            SELECT json_agg(url)::jsonb
            FROM (
                SELECT image_1_url AS url WHERE image_1_url IS NOT NULL
                UNION ALL
                SELECT image_2_url AS url WHERE image_2_url IS NOT NULL
                UNION ALL
                SELECT image_3_url AS url WHERE image_3_url IS NOT NULL
                UNION ALL
                SELECT image_4_url AS url WHERE image_4_url IS NOT NULL
            ) AS urls
            WHERE url IS NOT NULL
        )
        WHERE image_1_url IS NOT NULL
           OR image_2_url IS NOT NULL
           OR image_3_url IS NOT NULL
           OR image_4_url IS NOT NULL
    """))

    # Step 3: Drop old individual image URL columns
    op.drop_column('generation_results', 'image_4_url')
    op.drop_column('generation_results', 'image_3_url')
    op.drop_column('generation_results', 'image_2_url')
    op.drop_column('generation_results', 'image_1_url')


def downgrade():
    # WARNING: This downgrade has limitations:
    # - Can only restore up to 4 images (if JSONB array has more, extras are lost)
    # - If JSONB array has fewer than 4 images, remaining columns will be NULL

    # Step 1: Recreate the 4 individual image URL columns
    op.add_column('generation_results', sa.Column('image_1_url', sa.Text(), nullable=True))
    op.add_column('generation_results', sa.Column('image_2_url', sa.Text(), nullable=True))
    op.add_column('generation_results', sa.Column('image_3_url', sa.Text(), nullable=True))
    op.add_column('generation_results', sa.Column('image_4_url', sa.Text(), nullable=True))

    # Step 2: Migrate data back from JSONB array to individual columns
    connection = op.get_bind()

    # Extract first 4 elements from JSONB array into individual columns
    connection.execute(sa.text("""
        UPDATE generation_results
        SET
            image_1_url = images->0,
            image_2_url = images->1,
            image_3_url = images->2,
            image_4_url = images->3
        WHERE images IS NOT NULL AND jsonb_array_length(images) > 0
    """))

    # Step 3: Drop the JSONB images column
    op.drop_column('generation_results', 'images')
