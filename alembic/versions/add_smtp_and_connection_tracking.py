"""Add SMTP settings and connection tracking

Revision ID: add_smtp_connection_tracking
Revises: add_otp_email_verified
Create Date: 2025-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_smtp_connection_tracking'
down_revision: Union[str, None] = 'add_otp_email_verified'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create smtp_settings table for SMTP configuration
    # Can be global (org_id = NULL) or per-organization
    op.create_table(
        'smtp_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('org_id', sa.Integer(), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=True),
        sa.Column('smtp_server', sa.String(), nullable=False),
        sa.Column('smtp_port', sa.Integer(), nullable=False),
        sa.Column('smtp_username', sa.String(), nullable=False),
        sa.Column('smtp_password', sa.String(), nullable=False),  # Should be encrypted in production
        sa.Column('from_email', sa.String(), nullable=False),
        sa.Column('use_tls', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('org_id', name='uq_smtp_settings_org_id')  # One SMTP config per org
    )
    op.create_index(op.f('ix_smtp_settings_org_id'), 'smtp_settings', ['org_id'], unique=False)
    
    # Create connection_status table to track WebSocket connections and heartbeat
    op.create_table(
        'connection_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('org_id', sa.Integer(), sa.ForeignKey('organization.id', ondelete='CASCADE'), nullable=False),
        sa.Column('virtual_ip', sa.String(), nullable=False),
        sa.Column('peer_id', sa.String(), nullable=True),
        sa.Column('connection_id', sa.String(), nullable=True),
        sa.Column('public_ip', sa.String(), nullable=True),
        sa.Column('public_port', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='connected'),  # connected, disconnected, timeout
        sa.Column('connected_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('disconnected_at', sa.DateTime(), nullable=True),
        sa.Column('last_ping_at', sa.DateTime(), nullable=True),
        sa.Column('last_pong_at', sa.DateTime(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_connection_status_user_id'), 'connection_status', ['user_id'], unique=False)
    op.create_index(op.f('ix_connection_status_org_id'), 'connection_status', ['org_id'], unique=False)
    op.create_index(op.f('ix_connection_status_virtual_ip'), 'connection_status', ['virtual_ip'], unique=False)
    op.create_index(op.f('ix_connection_status_status'), 'connection_status', ['status'], unique=False)
    op.create_index(op.f('ix_connection_status_last_seen_at'), 'connection_status', ['last_seen_at'], unique=False)
    
    # Add last_seen_at column to virtual_ip_mapping for quick lookup
    op.add_column('virtual_ip_mapping', sa.Column('last_seen_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove last_seen_at from virtual_ip_mapping
    op.drop_column('virtual_ip_mapping', 'last_seen_at')
    
    # Drop connection_status table
    op.drop_index(op.f('ix_connection_status_last_seen_at'), table_name='connection_status')
    op.drop_index(op.f('ix_connection_status_status'), table_name='connection_status')
    op.drop_index(op.f('ix_connection_status_virtual_ip'), table_name='connection_status')
    op.drop_index(op.f('ix_connection_status_org_id'), table_name='connection_status')
    op.drop_index(op.f('ix_connection_status_user_id'), table_name='connection_status')
    op.drop_table('connection_status')
    
    # Drop smtp_settings table
    op.drop_index(op.f('ix_smtp_settings_org_id'), table_name='smtp_settings')
    op.drop_table('smtp_settings')

