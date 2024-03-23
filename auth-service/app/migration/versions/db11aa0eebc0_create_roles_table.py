"""Create roles table

Revision ID: db11aa0eebc0
Revises: 3e4ce8799f22
Create Date: 2024-03-23 15:21:02.097917

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db11aa0eebc0'
down_revision: Union[str, None] = '3e4ce8799f22'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Этот код будет выполнен при применении миграции
def upgrade():
    op.create_table(
        'roles',
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('name')
    )

    roles_data = [
        {"name": "<super_admin_role_name>", "description": "<super_admin_role_description>"},
        {"name": "<admin_role_name>", "description": "<admin_role_description>"},
        {"name": "<user_role_name>", "description": "<user_role_description>"},
        {"name": "<subscriber_role_name>", "description": "<subscriber_role_description>"},
        {"name": "<guest_role_name>", "description": "<guest_role_description>"}
    ]

    op.bulk_insert('roles', roles_data)


# Этот код будет выполнен при откате миграции
def downgrade():
    op.drop_table('roles')
