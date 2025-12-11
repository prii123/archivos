"""remove_drive_cred_type_column

Revision ID: 26ca7dbacc24
Revises: 002
Create Date: 2025-12-10 22:19:10.470904

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '26ca7dbacc24'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Remove drive_cred_type column from admins table (now only using Service Account)
    op.drop_column('admins', 'drive_cred_type')


def downgrade() -> None:
    # Re-add drive_cred_type column if we need to rollback
    op.add_column('admins', sa.Column('drive_cred_type', sa.String(), nullable=True))
