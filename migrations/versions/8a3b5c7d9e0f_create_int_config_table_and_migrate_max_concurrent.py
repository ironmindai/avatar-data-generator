"""create_int_config_table_and_migrate_max_concurrent

Revision ID: 8a3b5c7d9e0f
Revises: 7e1fabd32d40
Create Date: 2026-02-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '8a3b5c7d9e0f'
down_revision = '7e1fabd32d40'
branch_labels = None
depends_on = None


def upgrade():
    # Create int_config table for integer configuration values
    op.create_table(
        'int_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create index on key column
    op.create_index('ix_int_config_key', 'int_config', ['key'], unique=True)

    # Migrate max_concurrent_tasks from settings table to int_config table
    # First, check if the setting exists in settings table
    op.execute("""
        INSERT INTO int_config (key, value, created_at, updated_at)
        SELECT 'max_concurrent_tasks',
               CAST(value AS INTEGER),
               NOW(),
               NOW()
        FROM settings
        WHERE key = 'max_concurrent_tasks'
        ON CONFLICT (key) DO NOTHING
    """)

    # Delete max_concurrent_tasks from settings table if it exists
    op.execute("""
        DELETE FROM settings WHERE key = 'max_concurrent_tasks'
    """)

    # If no migration happened (setting didn't exist), insert default value
    op.execute("""
        INSERT INTO int_config (key, value, created_at, updated_at)
        SELECT 'max_concurrent_tasks', 1, NOW(), NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM int_config WHERE key = 'max_concurrent_tasks'
        )
    """)


def downgrade():
    # Migrate max_concurrent_tasks back to settings table
    op.execute("""
        INSERT INTO settings (key, value, created_at, updated_at)
        SELECT 'max_concurrent_tasks',
               CAST(value AS TEXT),
               NOW(),
               NOW()
        FROM int_config
        WHERE key = 'max_concurrent_tasks'
        ON CONFLICT (key) DO NOTHING
    """)

    # Drop index
    op.drop_index('ix_int_config_key', table_name='int_config')

    # Drop int_config table
    op.drop_table('int_config')
