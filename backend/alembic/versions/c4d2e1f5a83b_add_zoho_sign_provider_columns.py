"""add zoho sign provider columns

Revision ID: c4d2e1f5a83b
Revises: b3f1d9a4e25c
Create Date: 2026-10-31 23:45:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d2e1f5a83b'
down_revision: Union[str, Sequence[str], None] = 'b3f1d9a4e25c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add generic/Zoho Sign provider fields to agreement_signature_requests
    op.add_column(
        'agreement_signature_requests',
        sa.Column('provider_request_id', sa.String(length=100), nullable=True)
    )
    op.create_index(
        'ix_agreement_signature_requests_provider_request_id',
        'agreement_signature_requests',
        ['provider_request_id']
    )

    op.add_column(
        'agreement_signature_requests',
        sa.Column('provider_document_id', sa.String(length=100), nullable=True)
    )
    op.create_index(
        'ix_agreement_signature_requests_provider_document_id',
        'agreement_signature_requests',
        ['provider_document_id']
    )

    op.add_column(
        'agreement_signature_requests',
        sa.Column('provider_action_id', sa.String(length=100), nullable=True)
    )

    # Add provider_request_id to agreement_webhook_events
    op.add_column(
        'agreement_webhook_events',
        sa.Column('provider_request_id', sa.String(length=100), nullable=True)
    )
    op.create_index(
        'ix_agreement_webhook_events_provider_request_id',
        'agreement_webhook_events',
        ['provider_request_id']
    )


def downgrade() -> None:
    op.drop_index('ix_agreement_webhook_events_provider_request_id', table_name='agreement_webhook_events')
    op.drop_column('agreement_webhook_events', 'provider_request_id')

    op.drop_column('agreement_signature_requests', 'provider_action_id')
    op.drop_index('ix_agreement_signature_requests_provider_document_id', table_name='agreement_signature_requests')
    op.drop_column('agreement_signature_requests', 'provider_document_id')
    op.drop_index('ix_agreement_signature_requests_provider_request_id', table_name='agreement_signature_requests')
    op.drop_column('agreement_signature_requests', 'provider_request_id')
