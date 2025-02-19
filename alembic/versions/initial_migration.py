"""Initial database migration

Revision ID: initial_migration
Revises: 
Create Date: 2024-02-16 07:03:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create qr_codes table
    op.create_table('qr_codes',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('content', sa.String(length=2048), nullable=False),
        sa.Column('qr_type', sa.String(length=50), nullable=True),
        sa.Column('redirect_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('scan_count', sa.Integer(), nullable=True),
        sa.Column('last_scan_at', sa.DateTime(), nullable=True),
        sa.Column('fill_color', sa.String(length=50), nullable=True),
        sa.Column('back_color', sa.String(length=50), nullable=True),
        sa.Column('size', sa.Integer(), nullable=True),
        sa.Column('border', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_qr_codes_content'), 'qr_codes', ['content'], unique=False)
    op.create_index(op.f('ix_qr_codes_created_at'), 'qr_codes', ['created_at'], unique=False)
    op.create_index(op.f('ix_qr_codes_qr_type'), 'qr_codes', ['qr_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_qr_codes_qr_type'), table_name='qr_codes')
    op.drop_index(op.f('ix_qr_codes_created_at'), table_name='qr_codes')
    op.drop_index(op.f('ix_qr_codes_content'), table_name='qr_codes')
    op.drop_table('qr_codes') 