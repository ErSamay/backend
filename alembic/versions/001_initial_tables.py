"""Initial tables

Revision ID: 001
Revises: 
Create Date: 2025-09-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create videos table
    op.create_table('videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=False),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('fps', sa.Float(), nullable=True),
        sa.Column('upload_time', sa.DateTime(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('is_processed', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_videos_id'), 'videos', ['id'], unique=False)

    # Create trimmed_videos table
    op.create_table('trimmed_videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_video_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('duration', sa.Float(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['original_video_id'], ['videos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trimmed_videos_id'), 'trimmed_videos', ['id'], unique=False)

    # Create video_overlays table
    op.create_table('video_overlays',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('overlay_type', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(), nullable=True),
        sa.Column('x_position', sa.Integer(), nullable=True),
        sa.Column('y_position', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.Float(), nullable=True),
        sa.Column('end_time', sa.Float(), nullable=True),
        sa.Column('font_size', sa.Integer(), nullable=True),
        sa.Column('font_color', sa.String(), nullable=True),
        sa.Column('font_family', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_overlays_id'), 'video_overlays', ['id'], unique=False)

    # Create video_watermarks table
    op.create_table('video_watermarks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('watermark_path', sa.String(), nullable=False),
        sa.Column('x_position', sa.Integer(), nullable=True),
        sa.Column('y_position', sa.Integer(), nullable=True),
        sa.Column('opacity', sa.Float(), nullable=True),
        sa.Column('scale', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_watermarks_id'), 'video_watermarks', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_video_watermarks_id'), table_name='video_watermarks')
    op.drop_table('video_watermarks')
    op.drop_index(op.f('ix_video_overlays_id'), table_name='video_overlays')
    op.drop_table('video_overlays')
    op.drop_index(op.f('ix_trimmed_videos_id'), table_name='trimmed_videos')
    op.drop_table('trimmed_videos')
    op.drop_index(op.f('ix_videos_id'), table_name='videos')
    op.drop_table('videos')