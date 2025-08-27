"""Create initial database schema for FortunaMind persistence

Revision ID: 074c54636a56
Revises: 
Create Date: 2025-08-26 19:17:02.508778

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '074c54636a56'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create user_subscriptions table
    op.create_table(
        'user_subscriptions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('subscription_key', sa.String(255), nullable=True),
        sa.Column('tier', sa.String(50), nullable=False, server_default='free'),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_user_subscriptions_email')
    )
    
    # Create index on email for fast lookups
    op.create_index('idx_user_subscriptions_email', 'user_subscriptions', ['email'])
    
    # Create journal_entries table
    op.create_table(
        'journal_entries',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.String(64), nullable=False),
        sa.Column('entry', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on user_id for fast user-specific queries
    op.create_index('idx_journal_entries_user_id', 'journal_entries', ['user_id'])
    
    # Create user_preferences table
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.String(64), nullable=False),
        sa.Column('key', sa.String(255), nullable=False),
        sa.Column('value', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'key', name='uq_user_preferences_user_key')
    )
    
    # Create index on user_id for preferences
    op.create_index('idx_user_preferences_user_id', 'user_preferences', ['user_id'])
    
    # Create storage_records table (generic storage)
    op.create_table(
        'storage_records',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.String(64), nullable=False),
        sa.Column('record_type', sa.String(50), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes on storage_records
    op.create_index('idx_storage_records_user_id', 'storage_records', ['user_id'])
    op.create_index('idx_storage_records_type', 'storage_records', ['record_type'])
    op.create_index('idx_storage_records_user_type', 'storage_records', ['user_id', 'record_type'])
    
    # Enable Row Level Security (RLS) on all user data tables
    # Note: RLS policies will be created in a separate migration for better organization
    op.execute('ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY')  
    op.execute('ALTER TABLE storage_records ENABLE ROW LEVEL SECURITY')
    
    # user_subscriptions doesn't need RLS since it's managed by the system


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables in reverse order
    op.drop_table('storage_records')
    op.drop_table('user_preferences') 
    op.drop_table('journal_entries')
    op.drop_table('user_subscriptions')
