"""Delete password length limit

Revision ID: de1995308314
Revises: b0235593c93e
Create Date: 2026-01-28 14:23:24.113649

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de1995308314'
down_revision: Union[str, Sequence[str], None] = 'b0235593c93e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
