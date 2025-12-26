"""fix fk types and numeric defaults

Revision ID: 467d32b0d1a9
Revises: 3772b5e709f5
Create Date: 2025-12-26 19:47:41.150693

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '467d32b0d1a9'
down_revision = '3772b5e709f5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Fix FK type mismatch and numeric defaults:
    1. Drop existing FK constraints
    2. Convert url_id columns from BIGINT to INTEGER
    3. Recreate FK constraints with explicit names and CASCADE
    4. Set numeric defaults for BIGINT counters
    """
    # Drop existing FK constraints (auto-generated names from Alembic)
    op.drop_constraint('url_visits_url_id_fkey', 'url_visits', type_='foreignkey')
    op.drop_constraint('url_daily_stats_url_id_fkey', 'url_daily_stats', type_='foreignkey')
    
    # Convert url_id columns from BIGINT to INTEGER
    op.alter_column('url_visits', 'url_id',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    postgresql_using='url_id::integer',
                    existing_nullable=False)
    
    op.alter_column('url_daily_stats', 'url_id',
                    existing_type=sa.BigInteger(),
                    type_=sa.Integer(),
                    postgresql_using='url_id::integer',
                    existing_nullable=False)
    
    # Recreate FK constraints with explicit names and CASCADE
    op.create_foreign_key('fk_url_visits_url_id_urls', 'url_visits', 'urls', 
                          ['url_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_url_daily_stats_url_id_urls', 'url_daily_stats', 'urls', 
                          ['url_id'], ['id'], ondelete='CASCADE')
    
    # Set numeric defaults for BIGINT counters
    op.alter_column('urls', 'visit_count',
                    existing_type=sa.BigInteger(),
                    server_default=sa.text('0'),
                    existing_nullable=False)
    
    op.alter_column('url_daily_stats', 'count',
                    existing_type=sa.BigInteger(),
                    server_default=sa.text('0'),
                    existing_nullable=False)


def downgrade() -> None:
    """
    Reverse the changes:
    1. Drop named FK constraints
    2. Convert url_id columns back to BIGINT
    3. Recreate FK constraints without explicit names
    4. Restore string defaults (if needed for compatibility)
    """
    # Drop named FK constraints
    op.drop_constraint('fk_url_visits_url_id_urls', 'url_visits', type_='foreignkey')
    op.drop_constraint('fk_url_daily_stats_url_id_urls', 'url_daily_stats', type_='foreignkey')
    
    # Convert url_id columns back to BIGINT
    op.alter_column('url_visits', 'url_id',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)
    
    op.alter_column('url_daily_stats', 'url_id',
                    existing_type=sa.Integer(),
                    type_=sa.BigInteger(),
                    existing_nullable=False)
    
    # Recreate FK constraints without names (as in previous migration)
    op.create_foreign_key(None, 'url_visits', 'urls', ['url_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'url_daily_stats', 'urls', ['url_id'], ['id'], ondelete='CASCADE')
    
    # Restore previous defaults (string '0' - though both work the same)
    op.alter_column('urls', 'visit_count',
                    existing_type=sa.BigInteger(),
                    server_default=sa.text("'0'"),
                    existing_nullable=False)
    
    op.alter_column('url_daily_stats', 'count',
                    existing_type=sa.BigInteger(),
                    server_default=sa.text("'0'"),
                    existing_nullable=False)
