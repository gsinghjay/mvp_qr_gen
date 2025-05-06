"""Add title and description columns to qr_codes table

Revision ID: add_title_description_columns
Revises: add_error_level_column
Create Date: 2024-06-04 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers
revision = "add_title_description_columns"
down_revision = "add_error_level_column"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add title column (nullable initially for backward compatibility)
    op.add_column(
        "qr_codes",
        sa.Column("title", sa.String(100), nullable=True)
    )
    
    # Add description column (nullable)
    op.add_column(
        "qr_codes",
        sa.Column("description", sa.Text(), nullable=True)
    )


def downgrade() -> None:
    # Drop the description column
    op.drop_column("qr_codes", "description")
    
    # Drop the title column
    op.drop_column("qr_codes", "title") 