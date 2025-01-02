"""rename_book_llm_columns

Revision ID: 002
Revises: 001
Create Date: 2024-12-29 21:06:02.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename ai_summary to summary
    op.alter_column('books', 'ai_summary',
                    new_column_name='summary',
                    existing_type=sa.Text)
    
    # Rename ai_qa to questions_and_answers
    op.alter_column('books', 'ai_qa',
                    new_column_name='questions_and_answers',
                    existing_type=sa.Text)


def downgrade() -> None:
    # Rename summary back to ai_summary
    op.alter_column('books', 'summary',
                    new_column_name='ai_summary',
                    existing_type=sa.Text)
    
    # Rename questions_and_answers back to ai_qa
    op.alter_column('books', 'questions_and_answers',
                    new_column_name='ai_qa',
                    existing_type=sa.Text)
