"""Add is_active column to user table

Revision ID: add_user_is_active
Revises: add_smtp_connection_tracking
Create Date: 2025-01-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_user_is_active'
down_revision: Union[str, None] = 'add_smtp_connection_tracking'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_active column to user table
    # Default: False - user chưa xác minh Gmail
    # Sau khi verify OTP → set True
    op.add_column(
        'user',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false')
    )
    # Set is_active = true for existing users who have email_verified = true
    op.execute(
        "UPDATE \"user\" SET is_active = true WHERE email_verified = true"
    )
    # Create index for faster queries (WHERE is_active = true)
    op.create_index(op.f('ix_user_is_active'), 'user', ['is_active'], unique=False)


def downgrade() -> None:
    # Drop index and column
    op.drop_index(op.f('ix_user_is_active'), table_name='user')
    op.drop_column('user', 'is_active')

