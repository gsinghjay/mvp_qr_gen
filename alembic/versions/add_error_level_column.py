"""Add error_level column to qr_codes table

Revision ID: add_error_level_column
Revises: timezone_aware_migration
Create Date: 2024-05-30 10:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_error_level_column"
down_revision = "timezone_aware_migration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add error_level column with default value 'm' (medium)
    op.add_column(
        "qr_codes",
        sa.Column("error_level", sa.String(1), nullable=False, server_default="m")
    )


def downgrade() -> None:
    # Drop the error_level column
    op.drop_column("qr_codes", "error_level") 