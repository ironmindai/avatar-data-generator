"""create_config_table_for_boolean_settings

Revision ID: d59663db64e2
Revises: 30c18b6939ce
Create Date: 2026-01-31 14:13:31.527237

Creates a new Config table for storing global boolean configuration settings.
This replaces the flawed design where boolean flags were added as columns to the Settings table.

The Config table structure:
- id: Integer primary key
- key: String(255), unique, not null, indexed - the config key
- value: Boolean, not null - the config value (TRUE/FALSE)
- created_at: DateTime, not null, default NOW()
- updated_at: DateTime, not null, default NOW(), onupdate NOW()

Initial data seeded:
- randomize_face_base: False - enables randomizing faces for base image generation
- randomize_face_gender_lock: False - when face randomization is on, locks to matching gender

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd59663db64e2'
down_revision = '30c18b6939ce'
branch_labels = None
depends_on = None


def upgrade():
    # Create config table
    op.create_table(
        'config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )

    # Create index on key column for faster lookups
    op.create_index('ix_config_key', 'config', ['key'], unique=True)

    # Seed initial config values
    op.execute("""
        INSERT INTO config (key, value, created_at, updated_at)
        VALUES
            ('randomize_face_base', FALSE, NOW(), NOW()),
            ('randomize_face_gender_lock', FALSE, NOW(), NOW())
    """)


def downgrade():
    # Drop the index
    op.drop_index('ix_config_key', table_name='config')

    # Drop the config table
    op.drop_table('config')
