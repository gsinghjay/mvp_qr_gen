"""add_scan_log_table_and_enhance_qr_code_stats

Revision ID: d59b26b7dd93
Revises: c10a8618571d
Create Date: 2025-05-13 18:41:47.142478

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd59b26b7dd93'
down_revision: Union[str, None] = 'c10a8618571d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to qr_codes table for enhanced tracking
    op.add_column('qr_codes', sa.Column('genuine_scan_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('qr_codes', sa.Column('first_genuine_scan_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('qr_codes', sa.Column('last_genuine_scan_at', sa.DateTime(timezone=True), nullable=True))
    
    # Create scan_logs table
    op.create_table('scan_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('qr_code_id', sa.String(), nullable=False),
        sa.Column('scanned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('raw_user_agent', sa.Text(), nullable=True),
        sa.Column('is_genuine_scan', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('device_family', sa.String(length=100), nullable=True),
        sa.Column('os_family', sa.String(length=50), nullable=True),
        sa.Column('os_version', sa.String(length=50), nullable=True),
        sa.Column('browser_family', sa.String(length=50), nullable=True),
        sa.Column('browser_version', sa.String(length=50), nullable=True),
        sa.Column('is_mobile', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_tablet', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_pc', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_bot', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(['qr_code_id'], ['qr_codes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for scan_logs table
    op.create_index(op.f('ix_scan_logs_id'), 'scan_logs', ['id'], unique=False)
    op.create_index(op.f('ix_scan_logs_qr_code_id'), 'scan_logs', ['qr_code_id'], unique=False)
    op.create_index(op.f('ix_scan_logs_scanned_at'), 'scan_logs', ['scanned_at'], unique=False)
    op.create_index(op.f('ix_scan_logs_is_genuine_scan'), 'scan_logs', ['is_genuine_scan'], unique=False)
    op.create_index(op.f('ix_scan_logs_device_family'), 'scan_logs', ['device_family'], unique=False)
    op.create_index(op.f('ix_scan_logs_os_family'), 'scan_logs', ['os_family'], unique=False)
    op.create_index(op.f('ix_scan_logs_browser_family'), 'scan_logs', ['browser_family'], unique=False)
    op.create_index(op.f('ix_scan_logs_is_mobile'), 'scan_logs', ['is_mobile'], unique=False)
    op.create_index(op.f('ix_scan_logs_is_tablet'), 'scan_logs', ['is_tablet'], unique=False)
    op.create_index(op.f('ix_scan_logs_is_pc'), 'scan_logs', ['is_pc'], unique=False)
    op.create_index(op.f('ix_scan_logs_is_bot'), 'scan_logs', ['is_bot'], unique=False)


def downgrade() -> None:
    # Drop the scan_logs table and its indexes
    op.drop_table('scan_logs')
    
    # Remove the new columns from qr_codes table
    op.drop_column('qr_codes', 'genuine_scan_count')
    op.drop_column('qr_codes', 'first_genuine_scan_at')
    op.drop_column('qr_codes', 'last_genuine_scan_at') 