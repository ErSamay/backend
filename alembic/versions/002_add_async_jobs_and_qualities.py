"""Add async jobs and video qualities tables

Revision ID: 002
Revises: 001
Create Date: 2025-09-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get database connection
    connection = op.get_bind()
    
    # Create ENUMs only if they don't exist
    
    # Check and create jobstatus enum
    result = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'jobstatus'")
    ).fetchone()
    if not result:
        connection.execute(
            sa.text("CREATE TYPE jobstatus AS ENUM ('pending', 'processing', 'completed', 'failed')")
        )
    
    # Check and create jobtype enum
    result = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'jobtype'")
    ).fetchone()
    if not result:
        connection.execute(
            sa.text("CREATE TYPE jobtype AS ENUM ('upload_process', 'trim', 'text_overlay', 'image_overlay', 'video_overlay', 'watermark', 'quality_conversion')")
        )
    
    # Check and create videoquality enum
    result = connection.execute(
        sa.text("SELECT 1 FROM pg_type WHERE typname = 'videoquality'")
    ).fetchone()
    if not result:
        connection.execute(
            sa.text("CREATE TYPE videoquality AS ENUM ('1080p', '720p', '480p', '360p')")
        )
    
    # Create processing_jobs table
    # Use postgresql.ENUM with existing=True to reference existing enum types
    op.create_table('processing_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('job_type', postgresql.ENUM('upload_process', 'trim', 'text_overlay', 'image_overlay', 'video_overlay', 'watermark', 'quality_conversion', name='jobtype', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='jobstatus', create_type=False), nullable=True),
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('input_data', sa.Text(), nullable=True),
        sa.Column('result_data', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_processing_jobs_id'), 'processing_jobs', ['id'], unique=False)
    
    # Create video_variants table
    op.create_table('video_variants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_video_id', sa.Integer(), nullable=False),
        sa.Column('quality', postgresql.ENUM('1080p', '720p', '480p', '360p', name='videoquality', create_type=False), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('bitrate', sa.String(), nullable=True),
        sa.Column('is_processing', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['original_video_id'], ['videos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_variants_id'), 'video_variants', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_video_variants_id'), table_name='video_variants')
    op.drop_table('video_variants')
    op.drop_index(op.f('ix_processing_jobs_id'), table_name='processing_jobs')
    op.drop_table('processing_jobs')
    
    # Drop enums safely
    connection = op.get_bind()
    
    try:
        connection.execute(sa.text("DROP TYPE IF EXISTS videoquality CASCADE"))
    except:
        pass
    
    try:
        connection.execute(sa.text("DROP TYPE IF EXISTS jobtype CASCADE"))
    except:
        pass
    
    try:
        connection.execute(sa.text("DROP TYPE IF EXISTS jobstatus CASCADE"))
    except:
        pass