"""Add quality column to video_variants

Revision ID: d534d8c247d2
Revises: 004
Create Date: 2025-01-20 xx:xx:xx.xxxxxx

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd534d8c247d2'
down_revision = '004'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # First add column as nullable with default value
    op.add_column('video_variants', 
        sa.Column('quality', 
                 sa.Enum('Q_1080P', 'Q_720P', 'Q_480P', 'Q_360P', name='videoquality', native_enum=False, length=10), 
                 nullable=True, 
                 server_default='Q_720P'))
    
    # Update all existing rows to have a quality value based on dimensions
    op.execute("""
        UPDATE video_variants 
        SET quality = CASE 
            WHEN width = 1920 AND height = 1080 THEN 'Q_1080P'
            WHEN width = 1280 AND height = 720 THEN 'Q_720P'
            WHEN width = 854 AND height = 480 THEN 'Q_480P'
            WHEN width = 640 AND height = 360 THEN 'Q_360P'
            ELSE 'Q_720P'
        END
        WHERE quality IS NULL
    """)
    
    # Now make the column NOT NULL
    op.alter_column('video_variants', 'quality', nullable=False)

def downgrade() -> None:
    op.drop_column('video_variants', 'quality')