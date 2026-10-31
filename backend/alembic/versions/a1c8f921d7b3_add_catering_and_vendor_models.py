"""add_catering_and_vendor_models

Revision ID: a1c8f921d7b3
Revises: f82054a1d934
Create Date: 2026-11-01 00:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c8f921d7b3'
down_revision: Union[str, Sequence[str], None] = 'f82054a1d934'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create vendors table
    op.create_table(
        'vendors',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('category', sa.String(length=50), server_default='Catering', nullable=False),
        sa.Column('contact_person', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), server_default='Jaipur', nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('rating', sa.Numeric(precision=3, scale=2), server_default='5.00', nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vendors_id'), 'vendors', ['id'], unique=False)
    op.create_index(op.f('ix_vendors_name'), 'vendors', ['name'], unique=False)
    op.create_index(op.f('ix_vendors_category'), 'vendors', ['category'], unique=False)
    op.create_index(op.f('ix_vendors_phone'), 'vendors', ['phone'], unique=False)
    op.create_index(op.f('ix_vendors_is_active'), 'vendors', ['is_active'], unique=False)

    # 2. Create catering_plans table
    op.create_table(
        'catering_plans',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('project_id', sa.String(length=50), nullable=False),
        sa.Column('function_id', sa.String(length=50), nullable=False),
        sa.Column('service_style', sa.String(length=100), server_default='Silver Platter Degustation', nullable=False),
        sa.Column('cuisine_preferences', sa.Text(), nullable=True),
        sa.Column('guest_count', sa.Integer(), server_default='100', nullable=False),
        sa.Column('veg_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('non_veg_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('jain_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('dietary_notes', sa.Text(), nullable=True),
        sa.Column('service_timings', sa.String(length=100), nullable=True),
        sa.Column('location', sa.String(length=255), nullable=True),
        sa.Column('budget', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False),
        sa.Column('selected_vendor_id', sa.String(length=50), nullable=True),
        sa.Column('agreed_cost', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Draft', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['wedding_projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['function_id'], ['wedding_functions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['selected_vendor_id'], ['vendors.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('function_id')
    )
    op.create_index(op.f('ix_catering_plans_id'), 'catering_plans', ['id'], unique=False)
    op.create_index(op.f('ix_catering_plans_project_id'), 'catering_plans', ['project_id'], unique=False)
    op.create_index(op.f('ix_catering_plans_function_id'), 'catering_plans', ['function_id'], unique=True)
    op.create_index(op.f('ix_catering_plans_selected_vendor_id'), 'catering_plans', ['selected_vendor_id'], unique=False)
    op.create_index(op.f('ix_catering_plans_status'), 'catering_plans', ['status'], unique=False)

    # 3. Create catering_menu_items table
    op.create_table(
        'catering_menu_items',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('catering_plan_id', sa.String(length=50), nullable=False),
        sa.Column('course_category', sa.String(length=100), nullable=False),
        sa.Column('item_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('dietary_tag', sa.String(length=50), server_default='Vegetarian', nullable=False),
        sa.Column('quantity_note', sa.String(length=150), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['catering_plan_id'], ['catering_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_catering_menu_items_id'), 'catering_menu_items', ['id'], unique=False)
    op.create_index(op.f('ix_catering_menu_items_catering_plan_id'), 'catering_menu_items', ['catering_plan_id'], unique=False)
    op.create_index(op.f('ix_catering_menu_items_course_category'), 'catering_menu_items', ['course_category'], unique=False)

    # 4. Create catering_quotations table
    op.create_table(
        'catering_quotations',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('catering_plan_id', sa.String(length=50), nullable=False),
        sa.Column('vendor_id', sa.String(length=50), nullable=False),
        sa.Column('quotation_reference', sa.String(length=100), nullable=True),
        sa.Column('per_person_rate', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False),
        sa.Column('total_guest_count', sa.Integer(), server_default='100', nullable=False),
        sa.Column('food_subtotal', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False),
        sa.Column('equipment_charges', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False),
        sa.Column('gst_rate_percent', sa.Numeric(precision=5, scale=2), server_default='18.00', nullable=False),
        sa.Column('gst_amount', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Received', nullable=False),
        sa.Column('validity_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['catering_plan_id'], ['catering_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_catering_quotations_id'), 'catering_quotations', ['id'], unique=False)
    op.create_index(op.f('ix_catering_quotations_catering_plan_id'), 'catering_quotations', ['catering_plan_id'], unique=False)
    op.create_index(op.f('ix_catering_quotations_vendor_id'), 'catering_quotations', ['vendor_id'], unique=False)
    op.create_index(op.f('ix_catering_quotations_status'), 'catering_quotations', ['status'], unique=False)

    # 5. Create catering_communications table
    op.create_table(
        'catering_communications',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('catering_plan_id', sa.String(length=50), nullable=False),
        sa.Column('vendor_id', sa.String(length=50), nullable=True),
        sa.Column('communication_type', sa.String(length=50), server_default='WhatsApp Manual Share', nullable=False),
        sa.Column('recipient_phone', sa.String(length=50), nullable=True),
        sa.Column('message_text', sa.Text(), nullable=True),
        sa.Column('pdf_download_url', sa.String(length=500), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Initiated', nullable=False),
        sa.Column('initiated_by', sa.String(length=100), server_default='Agency Staff', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['catering_plan_id'], ['catering_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vendor_id'], ['vendors.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_catering_communications_id'), 'catering_communications', ['id'], unique=False)
    op.create_index(op.f('ix_catering_communications_catering_plan_id'), 'catering_communications', ['catering_plan_id'], unique=False)
    op.create_index(op.f('ix_catering_communications_vendor_id'), 'catering_communications', ['vendor_id'], unique=False)
    op.create_index(op.f('ix_catering_communications_status'), 'catering_communications', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('catering_communications')
    op.drop_table('catering_quotations')
    op.drop_table('catering_menu_items')
    op.drop_table('catering_plans')
    op.drop_table('vendors')

