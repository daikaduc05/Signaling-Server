"""Add OTP verification and email verified

Revision ID: add_otp_email_verified
Revises: 7e72e27993c0
Create Date: 2025-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'add_otp_email_verified'
down_revision: Union[str, None] = '7e72e27993c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add email_verified column to user table
    op.add_column('user', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))
    
    # Create otp_verification table
    op.create_table(
        'otp_verification',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('otp_code', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_otp_verification_email'), 'otp_verification', ['email'], unique=False)


def downgrade() -> None:
    # Drop index and table
    op.drop_index(op.f('ix_otp_verification_email'), table_name='otp_verification')
    op.drop_table('otp_verification')
    
    # Remove email_verified column
    op.drop_column('user', 'email_verified')

