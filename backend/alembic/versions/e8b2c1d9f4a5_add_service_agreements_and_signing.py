"""add service agreements and signing tables

Revision ID: e8b2c1d9f4a5
Revises: a1c8f921d7b3
Create Date: 2026-11-01 03:54:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e8b2c1d9f4a5'
down_revision = 'a1c8f921d7b3'
branch_labels = None
depends_on = None


def upgrade():
    # 1. service_agreements table
    op.create_table(
        'service_agreements',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('agreement_number', sa.String(length=50), nullable=False),
        sa.Column('client_id', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='DRAFT'),
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
        sa.Column('agreement_version', sa.String(length=20), nullable=False, server_default='v1.0'),
        sa.Column('is_internally_approved', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('approved_by', sa.String(length=150), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_by', sa.String(length=150), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('signed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('signed_by_name', sa.String(length=150), nullable=True),
        sa.Column('signed_by_email', sa.String(length=255), nullable=True),
        sa.Column('signature_data', sa.Text(), nullable=True),
        sa.Column('signer_ip', sa.String(length=50), nullable=True),
        sa.Column('signer_user_agent', sa.String(length=500), nullable=True),
        sa.Column('signed_pdf_path', sa.String(length=500), nullable=True),
        sa.Column('signing_otp_hash', sa.String(length=64), nullable=True),
        sa.Column('signing_otp_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('signing_otp_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('signing_otp_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('consent_confirmed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_by', sa.String(length=150), nullable=False, server_default='Agency Concierge'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agreement_number')
    )
    op.create_index(op.f('ix_service_agreements_id'), 'service_agreements', ['id'], unique=False)
    op.create_index(op.f('ix_service_agreements_agreement_number'), 'service_agreements', ['agreement_number'], unique=True)
    op.create_index(op.f('ix_service_agreements_client_id'), 'service_agreements', ['client_id'], unique=False)
    op.create_index(op.f('ix_service_agreements_status'), 'service_agreements', ['status'], unique=False)

    # 2. agreement_payment_milestones table
    op.create_table(
        'agreement_payment_milestones',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('agreement_id', sa.String(length=50), nullable=False),
        sa.Column('milestone_name', sa.String(length=100), nullable=False),
        sa.Column('percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('due_description', sa.String(length=255), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('sequence_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agreement_id'], ['service_agreements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agreement_payment_milestones_id'), 'agreement_payment_milestones', ['id'], unique=False)
    op.create_index(op.f('ix_agreement_payment_milestones_agreement_id'), 'agreement_payment_milestones', ['agreement_id'], unique=False)

    # 3. agreement_documents table
    op.create_table(
        'agreement_documents',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('agreement_id', sa.String(length=50), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mime_type', sa.String(length=100), nullable=False, server_default='application/pdf'),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['agreement_id'], ['service_agreements.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agreement_documents_id'), 'agreement_documents', ['id'], unique=False)
    op.create_index(op.f('ix_agreement_documents_agreement_id'), 'agreement_documents', ['agreement_id'], unique=False)

    # 4. agreement_status_history table
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


def downgrade():
    op.drop_table('agreement_status_history')
    op.drop_table('agreement_documents')
    op.drop_table('agreement_payment_milestones')
    op.drop_table('service_agreements')

