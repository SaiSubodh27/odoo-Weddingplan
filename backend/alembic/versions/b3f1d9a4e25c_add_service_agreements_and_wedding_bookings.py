"""add service agreements and wedding bookings for Phase 2

Revision ID: b3f1d9a4e25c
Revises: 84f8e25ce92c
Create Date: 2026-10-31 18:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3f1d9a4e25c'
down_revision: Union[str, Sequence[str], None] = '84f8e25ce92c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. service_agreements
    op.create_table(
        'service_agreements',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('agreement_number', sa.String(length=50), nullable=False),
        sa.Column('client_id', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
        sa.Column('signing_status', sa.String(length=50), nullable=False, server_default='NOT_CREATED'),
        sa.Column('wedding_date', sa.Date(), nullable=False),
        sa.Column('wedding_location', sa.String(length=255), nullable=False),
        sa.Column('venue', sa.String(length=255), nullable=True),
        sa.Column('guest_count', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('wedding_functions', sa.JSON(), nullable=True),
        sa.Column('service_package', sa.String(length=100), nullable=False, server_default='Royal Palace Grandeur'),
        sa.Column('included_services', sa.JSON(), nullable=True),
        sa.Column('excluded_services', sa.JSON(), nullable=True),
        sa.Column('deliverables', sa.JSON(), nullable=True),
        sa.Column('additional_terms', sa.Text(), nullable=True),
        sa.Column('package_price', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('tax_percentage', sa.Numeric(precision=5, scale=2), nullable=False, server_default='18.00'),
        sa.Column('tax_amount', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('discount_amount', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0.00'),
        sa.Column('currency', sa.String(length=10), nullable=False, server_default='INR'),
        sa.Column('current_version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_internally_approved', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('approved_by', sa.String(length=150), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('verified_by', sa.String(length=150), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_by', sa.String(length=150), nullable=False, server_default='Agency Concierge'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_service_agreements_id'), 'service_agreements', ['id'], unique=False)
    op.create_index(op.f('ix_service_agreements_agreement_number'), 'service_agreements', ['agreement_number'], unique=True)
    op.create_index(op.f('ix_service_agreements_client_id'), 'service_agreements', ['client_id'], unique=False)
    op.create_index(op.f('ix_service_agreements_status'), 'service_agreements', ['status'], unique=False)
    op.create_index(op.f('ix_service_agreements_signing_status'), 'service_agreements', ['signing_status'], unique=False)
    op.create_index(op.f('ix_service_agreements_is_deleted'), 'service_agreements', ['is_deleted'], unique=False)

    # 2. service_agreement_versions
    op.create_table(
        'service_agreement_versions',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('agreement_id', sa.String(length=50), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('snapshot_data', sa.JSON(), nullable=False),
        sa.Column('pdf_document_id', sa.String(length=50), nullable=True),
        sa.Column('pdf_hash_sha256', sa.String(length=64), nullable=True),
        sa.Column('pdf_file_path', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
        sa.Column('revision_reason', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=150), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agreement_id'], ['service_agreements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_service_agreement_versions_id'), 'service_agreement_versions', ['id'], unique=False)
    op.create_index(op.f('ix_service_agreement_versions_agreement_id'), 'service_agreement_versions', ['agreement_id'], unique=False)

    # 3. agreement_payment_milestones
    op.create_table(
        'agreement_payment_milestones',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('agreement_id', sa.String(length=50), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('sequence_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['agreement_id'], ['service_agreements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agreement_payment_milestones_id'), 'agreement_payment_milestones', ['id'], unique=False)
    op.create_index(op.f('ix_agreement_payment_milestones_agreement_id'), 'agreement_payment_milestones', ['agreement_id'], unique=False)

    # 4. agreement_documents
    op.create_table(
        'agreement_documents',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('agreement_id', sa.String(length=50), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('stored_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_hash_sha256', sa.String(length=64), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False, server_default='application/pdf'),
        sa.Column('source', sa.String(length=100), nullable=False, server_default='System'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agreement_id'], ['service_agreements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agreement_documents_id'), 'agreement_documents', ['id'], unique=False)
    op.create_index(op.f('ix_agreement_documents_agreement_id'), 'agreement_documents', ['agreement_id'], unique=False)
    op.create_index(op.f('ix_agreement_documents_document_type'), 'agreement_documents', ['document_type'], unique=False)
    op.create_index(op.f('ix_agreement_documents_file_hash_sha256'), 'agreement_documents', ['file_hash_sha256'], unique=False)

    # 5. agreement_signature_requests
    op.create_table(
        'agreement_signature_requests',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('agreement_id', sa.String(length=50), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('leegality_document_id', sa.String(length=100), nullable=True),
        sa.Column('leegality_request_id', sa.String(length=100), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=False, server_default='Leegality'),
        sa.Column('environment', sa.String(length=50), nullable=False, server_default='sandbox'),
        sa.Column('signer_name', sa.String(length=150), nullable=False),
        sa.Column('signer_email', sa.String(length=255), nullable=False),
        sa.Column('signer_phone', sa.String(length=50), nullable=True),
        sa.Column('signing_url', sa.Text(), nullable=True),
        sa.Column('signing_url_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='NOT_SENT'),
        sa.Column('raw_response', sa.JSON(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agreement_id'], ['service_agreements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agreement_signature_requests_id'), 'agreement_signature_requests', ['id'], unique=False)
    op.create_index(op.f('ix_agreement_signature_requests_agreement_id'), 'agreement_signature_requests', ['agreement_id'], unique=False)
    op.create_index(op.f('ix_agreement_signature_requests_leegality_document_id'), 'agreement_signature_requests', ['leegality_document_id'], unique=True)
    op.create_index(op.f('ix_agreement_signature_requests_status'), 'agreement_signature_requests', ['status'], unique=False)

    # 6. agreement_webhook_events
    op.create_table(
        'agreement_webhook_events',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('signature_request_id', sa.String(length=50), nullable=True),
        sa.Column('document_id', sa.String(length=100), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('mac_received', sa.String(length=150), nullable=True),
        sa.Column('mac_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('event_fingerprint', sa.String(length=64), nullable=False),
        sa.Column('raw_payload', sa.JSON(), nullable=False),
        sa.Column('is_processed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('processing_notes', sa.Text(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['signature_request_id'], ['agreement_signature_requests.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agreement_webhook_events_id'), 'agreement_webhook_events', ['id'], unique=False)
    op.create_index(op.f('ix_agreement_webhook_events_signature_request_id'), 'agreement_webhook_events', ['signature_request_id'], unique=False)
    op.create_index(op.f('ix_agreement_webhook_events_document_id'), 'agreement_webhook_events', ['document_id'], unique=False)
    op.create_index(op.f('ix_agreement_webhook_events_event_fingerprint'), 'agreement_webhook_events', ['event_fingerprint'], unique=True)

    # 7. agreement_status_history
    op.create_table(
        'agreement_status_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agreement_id', sa.String(length=50), nullable=False),
        sa.Column('from_status', sa.String(length=50), nullable=True),
        sa.Column('to_status', sa.String(length=50), nullable=False),
        sa.Column('changed_by', sa.String(length=150), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agreement_id'], ['service_agreements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agreement_status_history_agreement_id'), 'agreement_status_history', ['agreement_id'], unique=False)

    # 8. agreement_reviews
    op.create_table(
        'agreement_reviews',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('agreement_id', sa.String(length=50), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('reviewer_name', sa.String(length=150), nullable=False),
        sa.Column('decision', sa.String(length=50), nullable=False),
        sa.Column('remarks', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agreement_id'], ['service_agreements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agreement_reviews_id'), 'agreement_reviews', ['id'], unique=False)
    op.create_index(op.f('ix_agreement_reviews_agreement_id'), 'agreement_reviews', ['agreement_id'], unique=False)

    # 9. wedding_bookings
    op.create_table(
        'wedding_bookings',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('booking_reference', sa.String(length=50), nullable=False),
        sa.Column('client_id', sa.String(length=50), nullable=False),
        sa.Column('agreement_id', sa.String(length=50), nullable=False),
        sa.Column('confirmed_version_number', sa.Integer(), nullable=False),
        sa.Column('couple_title', sa.String(length=255), nullable=False),
        sa.Column('wedding_date', sa.Date(), nullable=False),
        sa.Column('wedding_location', sa.String(length=255), nullable=False),
        sa.Column('venue', sa.String(length=255), nullable=True),
        sa.Column('package_name', sa.String(length=100), nullable=False),
        sa.Column('confirmed_total_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('advance_amount_agreed', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('confirmed_by', sa.String(length=150), nullable=False),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('confirmation_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='CONFIRMED'),
        sa.Column('phase3_handoff_ready', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('phase3_handoff_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agreement_id'], ['service_agreements.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wedding_bookings_id'), 'wedding_bookings', ['id'], unique=False)
    op.create_index(op.f('ix_wedding_bookings_booking_reference'), 'wedding_bookings', ['booking_reference'], unique=True)
    op.create_index(op.f('ix_wedding_bookings_client_id'), 'wedding_bookings', ['client_id'], unique=False)
    op.create_index(op.f('ix_wedding_bookings_agreement_id'), 'wedding_bookings', ['agreement_id'], unique=True)
    op.create_index(op.f('ix_wedding_bookings_status'), 'wedding_bookings', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('wedding_bookings')
    op.drop_table('agreement_reviews')
    op.drop_table('agreement_status_history')
    op.drop_table('agreement_webhook_events')
    op.drop_table('agreement_signature_requests')
    op.drop_table('agreement_documents')
    op.drop_table('agreement_payment_milestones')
    op.drop_table('service_agreement_versions')
    op.drop_table('service_agreements')

