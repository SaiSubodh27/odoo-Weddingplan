"""add_google_forms_fields_to_client_registrations

Revision ID: 333dd530f18f
Revises: d54149825d53
Create Date: 2026-10-31 17:59:42.402220

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '333dd530f18f'
down_revision: Union[str, Sequence[str], None] = 'd54149825d53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Allow enquiry_id to be nullable (for unmatched Google Form submissions)
    op.alter_column('client_registrations', 'enquiry_id', existing_type=sa.String(length=50), nullable=True)

    # Drop existing unique constraint if present to allow multiple UNMATCHED (None) enquiry_ids
    try:
        op.drop_constraint('client_registrations_enquiry_id_key', 'client_registrations', type_='unique')
    except Exception:
        pass

    try:
        op.drop_index('ix_client_registrations_enquiry_id', table_name='client_registrations')
    except Exception:
        pass

    op.create_index(op.f('ix_client_registrations_enquiry_id'), 'client_registrations', ['enquiry_id'], unique=False)

    # 2. Add Google Forms and source tracking columns
    op.add_column('client_registrations', sa.Column('google_form_response_id', sa.String(length=100), nullable=True))
    op.add_column('client_registrations', sa.Column('google_sheet_row', sa.Integer(), nullable=True))
    op.add_column('client_registrations', sa.Column('enquiry_reference', sa.String(length=100), nullable=True))
    op.add_column('client_registrations', sa.Column('source', sa.String(length=50), nullable=False, server_default='Google Forms'))

    op.create_index(op.f('ix_client_registrations_google_form_response_id'), 'client_registrations', ['google_form_response_id'], unique=True)
    op.create_index(op.f('ix_client_registrations_enquiry_reference'), 'client_registrations', ['enquiry_reference'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_client_registrations_enquiry_reference'), table_name='client_registrations')
    op.drop_index(op.f('ix_client_registrations_google_form_response_id'), table_name='client_registrations')
    op.drop_column('client_registrations', 'source')
    op.drop_column('client_registrations', 'enquiry_reference')
    op.drop_column('client_registrations', 'google_sheet_row')
    op.drop_column('client_registrations', 'google_form_response_id')
    op.alter_column('client_registrations', 'enquiry_id', existing_type=sa.String(length=50), nullable=False)
