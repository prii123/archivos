"""Add user_id to admins and remove email

Revision ID: 002
Revises: 001
Create Date: 2025-12-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add user_id column to admins table
    op.add_column('admins', sa.Column('user_id', sa.Integer(), nullable=True))
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_admins_user_id_users',
        'admins', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Create unique index on user_id
    op.create_index('ix_admins_user_id', 'admins', ['user_id'], unique=True)
    
    # Drop old email column and index
    op.drop_index('ix_admins_email', table_name='admins')
    op.drop_column('admins', 'email')
    
    # Make user_id NOT NULL after data migration (if needed)
    # Note: In production, you would first populate user_id for existing admins
    # For new installations, we can make it NOT NULL immediately
    op.alter_column('admins', 'user_id', nullable=False)


def downgrade() -> None:
    # Add email column back
    op.add_column('admins', sa.Column('email', sa.String(), nullable=True))
    op.create_index('ix_admins_email', 'admins', ['email'], unique=True)
    
    # Drop user_id column and constraints
    op.drop_index('ix_admins_user_id', table_name='admins')
    op.drop_constraint('fk_admins_user_id_users', 'admins', type_='foreignkey')
    op.drop_column('admins', 'user_id')
