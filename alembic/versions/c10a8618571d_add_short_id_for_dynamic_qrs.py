"""add_short_id_for_dynamic_qrs

Revision ID: c10a8618571d
Revises: 17f4914834ef
Create Date: 2025-05-06 14:09:37.974885

"""
from typing import Sequence, Union
import uuid
import re

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = 'c10a8618571d'
down_revision: Union[str, None] = '17f4914834ef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Check if the short_id column already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('qr_codes')]
    
    # Only add column if it doesn't exist
    if 'short_id' not in columns:
        print("Adding short_id column...")
        # Add short_id column with appropriate constraints
        op.add_column(
            'qr_codes',
            sa.Column('short_id', sa.String(10), nullable=True, unique=True)
        )
        
        # Create an index on the short_id column for efficient lookups
        op.create_index('ix_qr_codes_short_id', 'qr_codes', ['short_id'])
    else:
        print("short_id column already exists")
    
    # 3. Set short_id for existing dynamic QR codes
    # Extract short_id from '/r/{short_id}' format in content column
    # This uses PostgreSQL's split_part function to extract the short_id part
    print("Populating short_id values for existing dynamic QR codes...")
    op.execute(
        text("""
        WITH to_update AS (
            SELECT id,
                   CASE
                       -- Extract the short_id from the content for URLs with the format "/r/{short_id}"
                       WHEN content LIKE '%/r/%' THEN
                           -- Use PostgreSQL's split_part to get the part after "/r/"
                           split_part(split_part(content, '/r/', 2), '/', 1)
                       -- For any other format, generate a new short_id
                       ELSE NULL
                   END AS new_short_id
            FROM qr_codes
            WHERE qr_type = 'dynamic' AND (short_id IS NULL OR short_id = '')
        )
        UPDATE qr_codes
        SET short_id = 
            CASE 
                -- Use the extracted short_id if available
                WHEN tu.new_short_id IS NOT NULL THEN tu.new_short_id
                -- Otherwise, generate a new UUID-based short_id
                ELSE substring(md5(random()::text) from 1 for 8)
            END
        FROM to_update tu
        WHERE qr_codes.id = tu.id
        AND (qr_codes.short_id IS NULL OR qr_codes.short_id = '')
        """)
    )


def downgrade() -> None:
    # Check if the short_id column exists before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('qr_codes')]
    
    if 'short_id' in columns:
        # Drop the index first if it exists
        if 'ix_qr_codes_short_id' in inspector.get_indexes('qr_codes'):
            op.drop_index('ix_qr_codes_short_id', table_name='qr_codes')
        
        # Drop the column
        op.drop_column('qr_codes', 'short_id')
        print("short_id column dropped")
    else:
        print("short_id column doesn't exist, nothing to drop") 