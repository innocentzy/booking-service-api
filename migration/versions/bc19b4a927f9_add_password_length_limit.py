"""Add password length limit

Revision ID: bc19b4a927f9
Revises: de1995308314
Create Date: 2026-01-28 14:32:45.389033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc19b4a927f9'
down_revision: Union[str, Sequence[str], None] = 'de1995308314'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
