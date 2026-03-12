"""add_face_count_to_dataset_images

Revision ID: 5999ec64f0aa
Revises: 9f2e3d4b6c8a
Create Date: 2026-03-12 11:47:09.649372

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5999ec64f0aa'
down_revision = '9f2e3d4b6c8a'
branch_labels = None
depends_on = None


def upgrade():
    # Add face_count column to dataset_images table
    # This stores the number of faces detected in each image using YuNet face detection
    # NULL = not yet analyzed, 0 = no faces, 1+ = number of faces detected
    op.add_column('dataset_images', sa.Column('face_count', sa.Integer(), nullable=True))

    # Add index on face_count for efficient filtering by face count
    op.create_index('ix_dataset_images_face_count', 'dataset_images', ['face_count'])


def downgrade():
    # Drop index first
    op.drop_index('ix_dataset_images_face_count', table_name='dataset_images')

    # Drop face_count column
    op.drop_column('dataset_images', 'face_count')
