from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Enum as SQLEnum
import enum
from datetime import datetime

Base = declarative_base()

# Enums
class JobStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobType(enum.Enum):
    UPLOAD_PROCESS = "upload_process"
    TRIM = "trim"
    TEXT_OVERLAY = "text_overlay"
    IMAGE_OVERLAY = "image_overlay"
    VIDEO_OVERLAY = "video_overlay"
    WATERMARK = "watermark"
    QUALITY_CONVERSION = "quality_conversion"

class VideoQuality(enum.Enum):
    Q_1080P = "1080p"
    Q_720P = "720p"
    Q_480P = "480p"
    Q_360P = "360p"

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    duration = Column(Float, nullable=True)  # in seconds
    file_size = Column(Integer, nullable=True)  # in bytes
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    fps = Column(Float, nullable=True)
    upload_time = Column(DateTime, default=datetime.utcnow)
    file_path = Column(String, nullable=False)
    is_processed = Column(Boolean, default=False)
    
    # Relationships
    trimmed_videos = relationship("TrimmedVideo", back_populates="original_video")
    overlays = relationship("VideoOverlay", back_populates="video")
    watermarks = relationship("VideoWatermark", back_populates="video")

class TrimmedVideo(Base):
    __tablename__ = "trimmed_videos"
    
    id = Column(Integer, primary_key=True, index=True)
    original_video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    filename = Column(String, nullable=False)
    start_time = Column(Float, nullable=False)  # in seconds
    end_time = Column(Float, nullable=False)    # in seconds
    duration = Column(Float, nullable=False)    # in seconds
    file_size = Column(Integer, nullable=True)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    original_video = relationship("Video", back_populates="trimmed_videos")

class VideoOverlay(Base):
    __tablename__ = "video_overlays"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    overlay_type = Column(String, nullable=False)  # 'text', 'image', 'video'
    content = Column(Text, nullable=True)  # For text overlays
    file_path = Column(String, nullable=True)  # For image/video overlays
    x_position = Column(Integer, default=0)
    y_position = Column(Integer, default=0)
    start_time = Column(Float, default=0.0)  # When overlay starts (seconds)
    end_time = Column(Float, nullable=True)   # When overlay ends (seconds)
    font_size = Column(Integer, nullable=True)  # For text overlays
    font_color = Column(String, nullable=True)  # For text overlays
    font_family = Column(String, nullable=True)  # For text overlays
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    video = relationship("Video", back_populates="overlays")

class VideoWatermark(Base):
    __tablename__ = "video_watermarks"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    watermark_path = Column(String, nullable=False)
    x_position = Column(Integer, default=10)
    y_position = Column(Integer, default=10)
    opacity = Column(Float, default=1.0)
    scale = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    video = relationship("Video", back_populates="watermarks")

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(String, primary_key=True)  # UUID
    job_type = Column(String, nullable=False)  # Changed from SQLEnum to String
    status = Column(String, default="pending")  # Changed from SQLEnum to String
    video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    input_data = Column(Text, nullable=True)  # JSON string for job parameters
    result_data = Column(Text, nullable=True)  # JSON string for results
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    video = relationship("Video", backref="processing_jobs")

class VideoVariant(Base):
    __tablename__ = "video_variants"
    
    id = Column(Integer, primary_key=True, index=True)
    original_video_id = Column(Integer, ForeignKey("videos.id"), nullable=False)
    quality = Column(String, nullable=False)  # Changed from SQLEnum to String
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    bitrate = Column(String, nullable=True)
    is_processing = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    original_video = relationship("Video", backref="variants")