"""create_settings_table

Revision ID: d8cfd3cb4083
Revises: 25698f3f906f
Create Date: 2026-01-30 11:33:28.266912

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd8cfd3cb4083'
down_revision = '25698f3f906f'
branch_labels = None
depends_on = None


def upgrade():
    # Create settings table
    op.create_table('settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create unique index on key column
    with op.batch_alter_table('settings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_settings_key'), ['key'], unique=True)

    # Insert default bio prompts
    op.execute("""
        INSERT INTO settings (key, value) VALUES
        ('bio_prompt_facebook', 'Write 2-4 sentences (150-250 characters) in first person that naturally explain what you do, why it matters, and include something human (location, passion, or personality quirk) - avoid corporate speak but don''t force casual, just write like you''re introducing yourself at a networking event.'),
        ('bio_prompt_instagram', 'Use 3-5 short lines (120-150 characters total) in first person with line breaks for readability - lead with what you do, add your angle or what makes you different, close with where to find you or what you''re building - conversational but not cutesy, professional but not stuffy, max 2 emojis if any.'),
        ('bio_prompt_x', 'Write 1-3 punchy sentences (under 160 characters) in first person that position your expertise and perspective - use your natural voice, include what you tweet about or care about, avoid buzzwords and corporate jargon but don''t try to be witty if that''s not you.'),
        ('bio_prompt_tiktok', 'Keep it 60-100 characters, first person, stating your niche and what people will see on your page - match the energy of your content (casual if casual, direct if direct), skip the formality entirely since this platform punishes corporate tone, no emojis unless they genuinely fit your vibe.')
    """)


def downgrade():
    # Drop the settings table
    with op.batch_alter_table('settings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_settings_key'))

    op.drop_table('settings')
