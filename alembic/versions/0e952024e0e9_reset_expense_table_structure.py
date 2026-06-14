"""Reset expense table structure

Revision ID: 0e952024e0e9
Revises: df7e20eb40c4
Create Date: 2025-07-19 02:24:46.448385
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0e952024e0e9'
down_revision: Union[str, Sequence[str], None] = 'df7e20eb40c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.alter_column(
            'user_id',
            existing_type=sa.INTEGER(),
            nullable=False
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.alter_column(
            'user_id',
            existing_type=sa.INTEGER(),
            nullable=True
        )

