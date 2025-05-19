"""create initial schema

Revision ID: 17f4914834ef
Revises: 
Create Date: 2025-05-06 12:21:29.371851

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17f4914834ef'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create QR codes table
    op.create_table('qr_codes',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('qr_type', sa.String(length=50), nullable=False, server_default=sa.text("'static'")),
        sa.Column('redirect_url', sa.Text(), nullable=True),
        sa.Column('short_id', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scan_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('last_scan_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('file_format', sa.String(length=10), nullable=False),
        sa.Column('fill_color', sa.String(length=50), nullable=False, server_default=sa.text("'black'")),
        sa.Column('back_color', sa.String(length=50), nullable=False, server_default=sa.text("'white'")),
        sa.Column('size', sa.Integer(), nullable=False, server_default=sa.text('10')),
        sa.Column('border', sa.Integer(), nullable=False, server_default=sa.text('4')),
        sa.Column('has_logo', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('error_level', sa.String(length=1), nullable=False, server_default=sa.text("'m'"))
    )
    
    # Create indices
    op.create_index(op.f('ix_qr_codes_id'), 'qr_codes', ['id'], unique=False)
    op.create_index(op.f('ix_qr_codes_short_id'), 'qr_codes', ['short_id'], unique=True)


def downgrade() -> None:
    # Drop indices
    op.drop_index(op.f('ix_qr_codes_short_id'), table_name='qr_codes')
    op.drop_index(op.f('ix_qr_codes_id'), table_name='qr_codes')
    
    # Drop table
    op.drop_table('qr_codes') 