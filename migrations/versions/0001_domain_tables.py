"""Initial evidence/result tables; JSON payloads retain complete provenance."""
from alembic import op
import sqlalchemy as sa
revision='0001'
down_revision=None
branch_labels=None
depends_on=None
NAMES=['sources','snapshots','runs','mappings','approvals','observations','entities','memberships','links','profiles','evaluations','artifacts','events','batches']
def upgrade():
    for name in NAMES:
        op.create_table(name,sa.Column('id',sa.String(128),primary_key=True),
            sa.Column('owner_id',sa.String(128),nullable=False),sa.Column('kind',sa.String(80),nullable=False),
            sa.Column('payload',sa.JSON(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False))
        op.create_index(f'ix_{name}_owner_id',name,['owner_id'])
        op.create_index(f'ix_{name}_kind',name,['kind'])
def downgrade():
    for name in reversed(NAMES):op.drop_table(name)
