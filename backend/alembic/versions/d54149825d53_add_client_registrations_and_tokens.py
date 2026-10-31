"""add_client_registrations_and_tokens

Revision ID: d54149825d53
Revises: 84f8e25ce92c
Create Date: 2026-10-31 16:59:45.035050

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd54149825d53'
down_revision: Union[str, Sequence[str], None] = '84f8e25ce92c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add registration token columns to enquiries
    op.add_column('enquiries', sa.Column('registration_token', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_enquiries_registration_token'), 'enquiries', ['registration_token'], unique=True)
    op.add_column('enquiries', sa.Column('registration_token_expires_at', sa.DateTime(timezone=True), nullable=True))

    # 2. Create client_registrations table
    op.create_table(
        'client_registrations',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('enquiry_id', sa.String(length=50), nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=False),
        sa.Column('partner_name', sa.String(length=150), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('wedding_date', sa.Date(), nullable=True),
        sa.Column('wedding_location', sa.String(length=255), nullable=True),
        sa.Column('expected_guest_count', sa.Integer(), nullable=True),
        sa.Column('estimated_budget', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('wedding_events', sa.Text(), nullable=True),
        sa.Column('preferred_theme', sa.String(length=255), nullable=True),
        sa.Column('service_package', sa.String(length=50), nullable=False, server_default='Full-Service'),
        sa.Column('preferences', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='SUBMITTED'),
        sa.Column('reviewed_by', sa.String(length=100), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('correction_notes', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['enquiry_id'], ['enquiries.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('enquiry_id')
    )
    op.create_index(op.f('ix_client_registrations_id'), 'client_registrations', ['id'], unique=False)
    op.create_index(op.f('ix_client_registrations_enquiry_id'), 'client_registrations', ['enquiry_id'], unique=True)
    op.create_index(op.f('ix_client_registrations_email'), 'client_registrations', ['email'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_client_registrations_email'), table_name='client_registrations')
    op.drop_index(op.f('ix_client_registrations_enquiry_id'), table_name='client_registrations')
    op.drop_index(op.f('ix_client_registrations_id'), table_name='client_registrations')
    op.drop_table('client_registrations')

    op.drop_column('enquiries', 'registration_token_expires_at')
    op.drop_index(op.f('ix_enquiries_registration_token'), table_name='enquiries')
    op.drop_column('enquiries', 'registration_token')
