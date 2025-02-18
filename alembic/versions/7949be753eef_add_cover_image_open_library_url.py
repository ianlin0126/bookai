"""add_cover_image_open_library_url

Revision ID: 7949be753eef
Revises: 003
Create Date: 2025-02-18 20:04:00.382634

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7949be753eef'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('books',
        sa.Column('cover_image_open_library_url', sa.String(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('books', 'cover_image_open_library_url')
