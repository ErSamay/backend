"""add missing columns to processing_jobs

Revision ID: 004
Revises: 002
Create Date: 2025-09-20 12:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '002'  # Use the revision ID from your last migration
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add missing columns to processing_jobs table
    op.add_column('processing_jobs', sa.Column('job_type', sa.String(50), nullable=False, server_default='upload_process'))
    op.add_column('processing_jobs', sa.Column('status', sa.String(20), nullable=False, server_default='pending'))

def downgrade() -> None:
    # Remove the columns if we need to rollback
    op.drop_column('processing_jobs', 'status')
    op.drop_column('processing_jobs', 'job_type')