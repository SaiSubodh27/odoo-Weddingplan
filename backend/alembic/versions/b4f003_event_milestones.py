"""Function attendance override and milestone accountability."""
from alembic import op
import sqlalchemy as sa
revision = 'b4f003'
down_revision = 'b4f002'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('wedding_functions') as batch:
        batch.add_column(sa.Column('guest_count_override', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('event_notes', sa.Text(), nullable=True))
    with op.batch_alter_table('project_milestones') as batch:
        batch.add_column(sa.Column('assigned_to', sa.String(50), nullable=True))
        batch.add_column(sa.Column('function_id', sa.String(50), nullable=True))
        batch.add_column(sa.Column('category', sa.String(80), nullable=False, server_default='General'))
        batch.create_foreign_key('fk_milestone_staff', 'user_accounts', ['assigned_to'], ['id'])
        batch.create_foreign_key('fk_milestone_function', 'wedding_functions', ['function_id'], ['id'])

def downgrade():
    with op.batch_alter_table('project_milestones') as batch:
        batch.drop_constraint('fk_milestone_function', type_='foreignkey')
        batch.drop_constraint('fk_milestone_staff', type_='foreignkey')
        batch.drop_column('category')
        batch.drop_column('function_id')
        batch.drop_column('assigned_to')
    with op.batch_alter_table('wedding_functions') as batch:
        batch.drop_column('event_notes')
        batch.drop_column('guest_count_override')
