"""rename2

Revision ID: 5e48fb9d97cc
Revises: 52f8fcb55b4d
Create Date: 2024-04-15 22:56:29.867768

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e48fb9d97cc'
down_revision: Union[str, None] = '52f8fcb55b4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('roles', sa.Column('name2', sa.String(length=255), nullable=False))
    op.drop_constraint('roles_name1_key', 'roles', type_='unique')
    op.create_unique_constraint(None, 'roles', ['name2'])
    op.drop_column('roles', 'name1')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('roles', sa.Column('name1', sa.VARCHAR(length=255), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'roles', type_='unique')
    op.create_unique_constraint('roles_name1_key', 'roles', ['name1'])
    op.drop_column('roles', 'name2')
    # ### end Alembic commands ###
