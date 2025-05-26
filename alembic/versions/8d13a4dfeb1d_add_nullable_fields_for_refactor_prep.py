"""add_nullable_fields_for_refactor_prep

Revision ID: 8d13a4dfeb1d
Revises: d59b26b7dd93
Create Date: 2025-05-26 01:36:33.537468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8d13a4dfeb1d'
down_revision: Union[str, None] = 'd59b26b7dd93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nullable fields for refactoring preparation.
    
    These fields will support future refactoring phases:
    - refactor_metadata: JSONB field for storing refactoring-related metadata
    - processed_by_new_service: Boolean flag for tracking service migration
    """
    # Add refactor_metadata JSONB column to qr_codes table
    op.add_column('qr_codes', sa.Column(
        'refactor_metadata', 
        postgresql.JSONB(astext_type=sa.Text()), 
        nullable=True, 
        server_default=sa.text("'{}'::jsonb")
    ))
    
    # Add processed_by_new_service Boolean column to scan_logs table
    op.add_column('scan_logs', sa.Column(
        'processed_by_new_service', 
        sa.Boolean(), 
        nullable=True, 
        server_default=sa.false()
    ))


def downgrade() -> None:
    """Remove nullable fields added for refactoring preparation."""
    # Remove processed_by_new_service column from scan_logs table
    op.drop_column('scan_logs', 'processed_by_new_service')
    
    # Remove refactor_metadata column from qr_codes table
    op.drop_column('qr_codes', 'refactor_metadata') 