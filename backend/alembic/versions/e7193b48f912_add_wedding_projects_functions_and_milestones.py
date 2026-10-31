"""add_wedding_projects_functions_and_milestones

Revision ID: e7193b48f912
Revises: d54149825d53
Create Date: 2026-10-31 18:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7193b48f912'
down_revision: Union[str, Sequence[str], None] = 'd54149825d53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create wedding_projects table
    op.create_table(
        'wedding_projects',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('project_code', sa.String(length=50), nullable=False),
        sa.Column('client_id', sa.String(length=50), nullable=False),
        sa.Column('booking_id', sa.String(length=50), nullable=True),
        sa.Column('project_name', sa.String(length=255), nullable=False),
        sa.Column('wedding_date', sa.Date(), nullable=False),
        sa.Column('location', sa.String(length=255), nullable=False),
        sa.Column('guest_count', sa.Integer(), server_default='100', nullable=False),
        sa.Column('estimated_budget', sa.Numeric(precision=15, scale=2), server_default='0.00', nullable=False),
        sa.Column('package_tier', sa.String(length=50), server_default='Full-Service', nullable=False),
        sa.Column('project_manager_name', sa.String(length=100), server_default='Maharani Gayatri Singh', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Planning', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wedding_projects_id'), 'wedding_projects', ['id'], unique=False)
    op.create_index(op.f('ix_wedding_projects_project_code'), 'wedding_projects', ['project_code'], unique=True)
    op.create_index(op.f('ix_wedding_projects_client_id'), 'wedding_projects', ['client_id'], unique=True)
    op.create_index(op.f('ix_wedding_projects_booking_id'), 'wedding_projects', ['booking_id'], unique=False)
    op.create_index(op.f('ix_wedding_projects_status'), 'wedding_projects', ['status'], unique=False)
    op.create_index(op.f('ix_wedding_projects_is_deleted'), 'wedding_projects', ['is_deleted'], unique=False)

    # 2. Create wedding_functions table
    op.create_table(
        'wedding_functions',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('project_id', sa.String(length=50), nullable=False),
        sa.Column('function_name', sa.String(length=100), nullable=False),
        sa.Column('function_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.String(length=20), nullable=True),
        sa.Column('end_time', sa.String(length=20), nullable=True),
        sa.Column('venue', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='Scheduled', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['wedding_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wedding_functions_id'), 'wedding_functions', ['id'], unique=False)
    op.create_index(op.f('ix_wedding_functions_project_id'), 'wedding_functions', ['project_id'], unique=False)

    # 3. Create project_milestones table
    op.create_table(
        'project_milestones',
        sa.Column('id', sa.String(length=50), nullable=False),
        sa.Column('project_id', sa.String(length=50), nullable=False),
        sa.Column('milestone_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Pending', nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['wedding_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_milestones_id'), 'project_milestones', ['id'], unique=False)
    op.create_index(op.f('ix_project_milestones_project_id'), 'project_milestones', ['project_id'], unique=False)

    # 4. Create project_status_history table
    op.create_table(
        'project_status_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('project_id', sa.String(length=50), nullable=False),
        sa.Column('old_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=False),
        sa.Column('changed_by', sa.String(length=100), server_default='Agency Staff', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['wedding_projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_project_status_history_project_id'), 'project_status_history', ['project_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_project_status_history_project_id'), table_name='project_status_history')
    op.drop_table('project_status_history')

    op.drop_index(op.f('ix_project_milestones_project_id'), table_name='project_milestones')
    op.drop_index(op.f('ix_project_milestones_id'), table_name='project_milestones')
    op.drop_table('project_milestones')

    op.drop_index(op.f('ix_wedding_functions_project_id'), table_name='wedding_functions')
    op.drop_index(op.f('ix_wedding_functions_id'), table_name='wedding_functions')
    op.drop_table('wedding_functions')

    op.drop_index(op.f('ix_wedding_projects_is_deleted'), table_name='wedding_projects')
    op.drop_index(op.f('ix_wedding_projects_status'), table_name='wedding_projects')
    op.drop_index(op.f('ix_wedding_projects_booking_id'), table_name='wedding_projects')
    op.drop_index(op.f('ix_wedding_projects_client_id'), table_name='wedding_projects')
    op.drop_index(op.f('ix_wedding_projects_project_code'), table_name='wedding_projects')
    op.drop_index(op.f('ix_wedding_projects_id'), table_name='wedding_projects')
    op.drop_table('wedding_projects')
