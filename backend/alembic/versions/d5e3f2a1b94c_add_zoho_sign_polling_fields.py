"""add zoho sign polling fields

Revision ID: d5e3f2a1b94c
Revises: c4d2e1f5a83b
Create Date: 2026-11-01 00:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5e3f2a1b94c'
down_revision: Union[str, Sequence[str], None] = 'c4d2e1f5a83b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add polling and status check fields to agreement_signature_requests
    op.add_column(
        'agreement_signature_requests',
        sa.Column('last_status_checked_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'agreement_signature_requests',
        sa.Column('next_status_check_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        'ix_agreement_signature_requests_next_status_check_at',
        'agreement_signature_requests',
        ['next_status_check_at']
    )
    op.add_column(
        'agreement_signature_requests',
        sa.Column('polling_attempt_count', sa.Integer(), nullable=False, server_default='0')
    )
    op.add_column(
        'agreement_signature_requests',
        sa.Column('last_polling_error', sa.Text(), nullable=True)
    )
    op.add_column(
        'agreement_signature_requests',
        sa.Column('provider_completed_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Also add last_status_checked_at to service_agreements for quick query/display
    op.add_column(
        'service_agreements',
        sa.Column('last_status_checked_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('service_agreements', 'last_status_checked_at')
    op.drop_column('agreement_signature_requests', 'provider_completed_at')
    op.drop_column('agreement_signature_requests', 'last_polling_error')
    op.drop_column('agreement_signature_requests', 'polling_attempt_count')
    op.drop_index('ix_agreement_signature_requests_next_status_check_at', table_name='agreement_signature_requests')
    op.drop_column('agreement_signature_requests', 'next_status_check_at')
    op.drop_column('agreement_signature_requests', 'last_status_checked_at')
