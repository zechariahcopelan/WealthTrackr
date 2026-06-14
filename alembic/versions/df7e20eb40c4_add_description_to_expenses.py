"""Add description to expenses

Revision ID: df7e20eb40c4
Revises: a32dbf1daa5c
Create Date: 2025-07-19 01:55:02.652501
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'df7e20eb40c4'
down_revision: Union[str, Sequence[str], None] = 'a32dbf1daa5c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """No-op because column already exists."""
    pass

def downgrade() -> None:
    """Drop the 'description' column only if it exists."""
    with op.batch_alter_table("expenses") as batch_op:
        batch_op.drop_column('description')


