"""Phase 4 operational plans and tasks.

Revision ID: b4f001
Revises: a1c8f921d7b3
"""
from alembic import op
import sqlalchemy as sa

revision = 'b4f001'
down_revision = 'a1c8f921d7b3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('wedding_plans',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('project_id', sa.String(50), sa.ForeignKey('wedding_projects.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('status', sa.String(30), nullable=False, server_default='Planning'),
        sa.Column('planning_start_date', sa.Date(), nullable=True),
        sa.Column('team_lead_id', sa.String(50), sa.ForeignKey('user_accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_wedding_plans_project_id', 'wedding_plans', ['project_id'], unique=True)
    op.create_table('wedding_plan_tasks',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('plan_id', sa.String(50), sa.ForeignKey('wedding_plans.id', ondelete='CASCADE'), nullable=False),
        sa.Column('function_id', sa.String(50), sa.ForeignKey('wedding_functions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(80), nullable=False, server_default='General'),
        sa.Column('priority', sa.String(20), nullable=False, server_default='Medium'),
        sa.Column('status', sa.String(30), nullable=False, server_default='To Do'),
        sa.Column('assigned_to', sa.String(50), sa.ForeignKey('user_accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    op.create_index('ix_wedding_plan_tasks_plan_id', 'wedding_plan_tasks', ['plan_id'])


def downgrade():
    op.drop_index('ix_wedding_plan_tasks_plan_id', table_name='wedding_plan_tasks')
    op.drop_table('wedding_plan_tasks')
    op.drop_index('ix_wedding_plans_project_id', table_name='wedding_plans')
    op.drop_table('wedding_plans')
