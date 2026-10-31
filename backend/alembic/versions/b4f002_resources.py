"""Phase 4 planning resources. Revision ID: b4f002; Revises: b4f001."""
from alembic import op
import sqlalchemy as sa
revision = 'b4f002'
down_revision = 'b4f001'
branch_labels = None
depends_on = None

PROJECT = sa.ForeignKey('wedding_projects.id', ondelete='CASCADE')
FUNCTION = sa.ForeignKey('wedding_functions.id', ondelete='SET NULL')

def base():
    return [sa.Column('id', sa.String(50), primary_key=True), sa.Column('project_id', sa.String(50), sa.ForeignKey('wedding_projects.id'), nullable=False)]

def upgrade():
    op.create_table('wedding_budget_allocations', *base(), sa.Column('category', sa.String(80), nullable=False), sa.Column('amount', sa.Numeric(15,2), nullable=False), sa.Column('notes', sa.Text()))
    op.create_table('wedding_expenses', *base(), sa.Column('category', sa.String(80), nullable=False), sa.Column('description', sa.String(255), nullable=False), sa.Column('amount', sa.Numeric(15,2), nullable=False), sa.Column('expense_date', sa.Date(), nullable=False), sa.Column('notes', sa.Text()))
    op.create_table('wedding_vendor_assignments', *base(), sa.Column('function_id', sa.String(50), sa.ForeignKey('wedding_functions.id')), sa.Column('vendor_id', sa.String(50), sa.ForeignKey('vendors.id'), nullable=False), sa.Column('category', sa.String(80), nullable=False), sa.Column('responsibility', sa.Text()), sa.Column('contract_amount', sa.Numeric(15,2), nullable=False), sa.Column('status', sa.String(40), nullable=False))
    op.create_table('wedding_accommodations', *base(), sa.Column('hotel_name', sa.String(255), nullable=False), sa.Column('room_type', sa.String(100), nullable=False), sa.Column('room_count', sa.Integer(), nullable=False), sa.Column('nightly_rate', sa.Numeric(15,2), nullable=False), sa.Column('check_in', sa.Date(), nullable=False), sa.Column('check_out', sa.Date(), nullable=False), sa.Column('status', sa.String(40), nullable=False), sa.Column('notes', sa.Text()))
    op.create_table('wedding_logistics', *base(), sa.Column('function_id', sa.String(50), sa.ForeignKey('wedding_functions.id')), sa.Column('service_type', sa.String(100), nullable=False), sa.Column('vehicle_type', sa.String(100), nullable=False), sa.Column('vehicle_count', sa.Integer(), nullable=False), sa.Column('pickup_location', sa.String(255), nullable=False), sa.Column('dropoff_location', sa.String(255), nullable=False), sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=False), sa.Column('driver_contact', sa.String(100)), sa.Column('status', sa.String(40), nullable=False), sa.Column('notes', sa.Text()))
    for name in ['wedding_budget_allocations', 'wedding_expenses', 'wedding_vendor_assignments', 'wedding_accommodations', 'wedding_logistics']:
        op.create_index('ix_' + name + '_project_id', name, ['project_id'])

def downgrade():
    for name in reversed(['wedding_budget_allocations', 'wedding_expenses', 'wedding_vendor_assignments', 'wedding_accommodations', 'wedding_logistics']):
        op.drop_index('ix_' + name + '_project_id', table_name=name)
        op.drop_table(name)
