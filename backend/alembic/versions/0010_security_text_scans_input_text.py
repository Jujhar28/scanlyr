"""Add input_text column to security_text_scans

Revision ID: 0010_scan_input_text
Revises: 0009_security_text_scans
Create Date: 2026-05-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_scan_input_text"
down_revision: str | Sequence[str] | None = "0009_security_text_scans"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("security_text_scans", sa.Column("input_text", sa.Text(), nullable=True))
    op.execute(
        """
        UPDATE security_text_scans
        SET input_text = REPLACE(input_preview, '…', '')
        WHERE input_text IS NULL
        """,
    )


def downgrade() -> None:
    op.drop_column("security_text_scans", "input_text")
