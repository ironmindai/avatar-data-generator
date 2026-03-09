"""create_image_datasets_tables

Revision ID: 562b42df8d87
Revises: a5b7c9d1e3f5
Create Date: 2026-03-09 11:08:47.741922

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '562b42df8d87'
down_revision = 'a5b7c9d1e3f5'
branch_labels = None
depends_on = None


def upgrade():
    # Create image_datasets table
    op.create_table(
        'image_datasets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='active'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='FALSE'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_image_datasets_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dataset_id', name='uq_image_datasets_dataset_id')
    )

    # Create indexes for image_datasets
    op.create_index('ix_image_datasets_dataset_id', 'image_datasets', ['dataset_id'], unique=True)
    op.create_index('ix_image_datasets_user_id', 'image_datasets', ['user_id'], unique=False)
    op.create_index('ix_image_datasets_status', 'image_datasets', ['status'], unique=False)
    op.create_index('ix_image_datasets_is_public', 'image_datasets', ['is_public'], unique=False)

    # Create dataset_images table
    op.create_table(
        'dataset_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.Text(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=True),
        sa.Column('source_id', sa.String(length=255), nullable=True),
        sa.Column('source_metadata', sa.JSON(), nullable=True),
        sa.Column('image_hash', sa.String(length=64), nullable=True),
        sa.Column('added_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['dataset_id'], ['image_datasets.id'], name='fk_dataset_images_dataset_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for dataset_images
    op.create_index('ix_dataset_images_dataset_id', 'dataset_images', ['dataset_id'], unique=False)
    op.create_index('ix_dataset_images_source_type', 'dataset_images', ['source_type'], unique=False)
    op.create_index('ix_dataset_images_source_id', 'dataset_images', ['source_id'], unique=False)
    op.create_index('ix_dataset_images_image_hash', 'dataset_images', ['image_hash'], unique=False)

    # Create dataset_permissions table
    op.create_table(
        'dataset_permissions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('permission_level', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['dataset_id'], ['image_datasets.id'], name='fk_dataset_permissions_dataset_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_dataset_permissions_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('dataset_id', 'user_id', name='uq_dataset_permissions_dataset_user')
    )

    # Create indexes for dataset_permissions
    op.create_index('ix_dataset_permissions_dataset_id', 'dataset_permissions', ['dataset_id'], unique=False)
    op.create_index('ix_dataset_permissions_user_id', 'dataset_permissions', ['user_id'], unique=False)


def downgrade():
    # Drop indexes for dataset_permissions
    op.drop_index('ix_dataset_permissions_user_id', table_name='dataset_permissions')
    op.drop_index('ix_dataset_permissions_dataset_id', table_name='dataset_permissions')

    # Drop dataset_permissions table
    op.drop_table('dataset_permissions')

    # Drop indexes for dataset_images
    op.drop_index('ix_dataset_images_image_hash', table_name='dataset_images')
    op.drop_index('ix_dataset_images_source_id', table_name='dataset_images')
    op.drop_index('ix_dataset_images_source_type', table_name='dataset_images')
    op.drop_index('ix_dataset_images_dataset_id', table_name='dataset_images')

    # Drop dataset_images table
    op.drop_table('dataset_images')

    # Drop indexes for image_datasets
    op.drop_index('ix_image_datasets_is_public', table_name='image_datasets')
    op.drop_index('ix_image_datasets_status', table_name='image_datasets')
    op.drop_index('ix_image_datasets_user_id', table_name='image_datasets')
    op.drop_index('ix_image_datasets_dataset_id', table_name='image_datasets')

    # Drop image_datasets table
    op.drop_table('image_datasets')
