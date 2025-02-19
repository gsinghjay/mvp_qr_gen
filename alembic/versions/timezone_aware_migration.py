"""Update datetime columns to be timezone-aware

Revision ID: timezone_aware_migration
Revises: initial_migration
Create Date: 2024-02-19 06:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = 'timezone_aware_migration'
down_revision = 'initial_migration'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update datetime columns to be timezone-aware and set proper defaults
    with op.batch_alter_table('qr_codes') as batch_op:
        # Temporarily allow nullable for the conversion
        batch_op.alter_column('created_at',
                            existing_type=sa.DateTime(),
                            type_=sa.DateTime(timezone=True),
                            existing_nullable=True)
        batch_op.alter_column('last_scan_at',
                            existing_type=sa.DateTime(),
                            type_=sa.DateTime(timezone=True),
                            existing_nullable=True)
        batch_op.alter_column('qr_type',
                            existing_type=sa.String(length=50),
                            server_default='static',
                            nullable=False)
        batch_op.alter_column('scan_count',
                            existing_type=sa.Integer(),
                            server_default='0',
                            nullable=False)
        batch_op.alter_column('fill_color',
                            existing_type=sa.String(length=50),
                            server_default='black',
                            nullable=False)
        batch_op.alter_column('back_color',
                            existing_type=sa.String(length=50),
                            server_default='white',
                            nullable=False)
        batch_op.alter_column('size',
                            existing_type=sa.Integer(),
                            server_default='10',
                            nullable=False)
        batch_op.alter_column('border',
                            existing_type=sa.Integer(),
                            server_default='4',
                            nullable=False)

def downgrade() -> None:
    with op.batch_alter_table('qr_codes') as batch_op:
        batch_op.alter_column('created_at',
                            existing_type=sa.DateTime(timezone=True),
                            type_=sa.DateTime(),
                            existing_nullable=True)
        batch_op.alter_column('last_scan_at',
                            existing_type=sa.DateTime(timezone=True),
                            type_=sa.DateTime(),
                            existing_nullable=True)
        batch_op.alter_column('qr_type',
                            existing_type=sa.String(length=50),
                            server_default=None,
                            nullable=True)
        batch_op.alter_column('scan_count',
                            existing_type=sa.Integer(),
                            server_default=None,
                            nullable=True)
        batch_op.alter_column('fill_color',
                            existing_type=sa.String(length=50),
                            server_default=None,
                            nullable=True)
        batch_op.alter_column('back_color',
                            existing_type=sa.String(length=50),
                            server_default=None,
                            nullable=True)
        batch_op.alter_column('size',
                            existing_type=sa.Integer(),
                            server_default=None,
                            nullable=True)
        batch_op.alter_column('border',
                            existing_type=sa.Integer(),
                            server_default=None,
                            nullable=True) 