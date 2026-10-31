"""Operational planning audit history."""
from alembic import op
import sqlalchemy as sa
revision = 'b4f004'
down_revision = 'b4f003'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('wedding_planning_audit',
        sa.Column('id', sa.String(50), primary_key=True),
        sa.Column('project_id', sa.String(50), sa.ForeignKey('wedding_projects.id'), nullable=False),
        sa.Column('resource_type', sa.String(80), nullable=False),
        sa.Column('record_id', sa.String(50), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('actor', sa.String(100), nullable=False),
        sa.Column('details', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    op.create_index('ix_wedding_planning_audit_project_id', 'wedding_planning_audit', ['project_id'])

def downgrade():
    op.drop_index('ix_wedding_planning_audit_project_id', table_name='wedding_planning_audit')
    op.drop_table('wedding_planning_audit')
