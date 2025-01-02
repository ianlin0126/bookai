"""add publication year

Revision ID: 003
Revises: 002
Create Date: 2025-01-02 22:16:55.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add publication_year column
    op.add_column('books', sa.Column('publication_year', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove publication_year column
    op.drop_column('books', 'publication_year')
