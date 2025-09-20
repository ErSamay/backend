from sqlalchemy.orm import Session
import models
import schemas
from typing import List, Optional
import uuid
import json
from datetime import datetime
from models import JobType, JobStatus, VideoQuality  # Import the enums

# Video CRUD operations
def create_video(db: Session, video: schemas.VideoCreate, file_path: str, 
                duration: Optional[float] = None, file_size: Optional[int] = None,
                width: Optional[int] = None, height: Optional[int] = None, 
                fps: Optional[float] = None) -> models.Video:
    db_video = models.Video(
        filename=video.filename,
        original_filename=video.original_filename,
        duration=duration,
        file_size=file_size,
        width=width,
        height=height,
        fps=fps,
        file_path=file_path
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

def get_video(db: Session, video_id: int) -> Optional[models.Video]:
    return db.query(models.Video).filter(models.Video.id == video_id).first()

def get_videos(db: Session, skip: int = 0, limit: int = 100) -> List[models.Video]:
    return db.query(models.Video).offset(skip).limit(limit).all()

def get_videos_count(db: Session) -> int:
    return db.query(models.Video).count()

def update_video_processed_status(db: Session, video_id: int, is_processed: bool = True):
    db.query(models.Video).filter(models.Video.id == video_id).update({"is_processed": is_processed})
    db.commit()

# Trimmed Video CRUD operations
def create_trimmed_video(db: Session, original_video_id: int, filename: str, 
                        file_path: str, start_time: float, end_time: float, 
                        duration: float, file_size: Optional[int] = None) -> models.TrimmedVideo:
    db_trimmed = models.TrimmedVideo(
        original_video_id=original_video_id,
        filename=filename,
        file_path=file_path,
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        file_size=file_size
    )
    db.add(db_trimmed)
    db.commit()
    db.refresh(db_trimmed)
    return db_trimmed

def get_trimmed_video(db: Session, trimmed_id: int) -> Optional[models.TrimmedVideo]:
    return db.query(models.TrimmedVideo).filter(models.TrimmedVideo.id == trimmed_id).first()

def get_trimmed_videos_by_original(db: Session, original_video_id: int) -> List[models.TrimmedVideo]:
    return db.query(models.TrimmedVideo).filter(
        models.TrimmedVideo.original_video_id == original_video_id
    ).all()

# Overlay CRUD operations
def create_text_overlay(db: Session, overlay_data: schemas.TextOverlayCreate) -> models.VideoOverlay:
    db_overlay = models.VideoOverlay(
        video_id=overlay_data.video_id,
        overlay_type=overlay_data.overlay_type.value,
        content=overlay_data.content,
        x_position=overlay_data.x_position,
        y_position=overlay_data.y_position,
        start_time=overlay_data.start_time,
        end_time=overlay_data.end_time,
        font_size=overlay_data.font_size,
        font_color=overlay_data.font_color,
        font_family=overlay_data.font_family
    )
    db.add(db_overlay)
    db.commit()
    db.refresh(db_overlay)
    return db_overlay

def create_file_overlay(db: Session, overlay_data: schemas.ImageOverlayCreate, 
                       file_path: str, overlay_type: str) -> models.VideoOverlay:
    db_overlay = models.VideoOverlay(
        video_id=overlay_data.video_id,
        overlay_type=overlay_type,
        file_path=file_path,
        x_position=overlay_data.x_position,
        y_position=overlay_data.y_position,
        start_time=overlay_data.start_time,
        end_time=overlay_data.end_time
    )
    db.add(db_overlay)
    db.commit()
    db.refresh(db_overlay)
    return db_overlay

def get_overlays_by_video(db: Session, video_id: int) -> List[models.VideoOverlay]:
    return db.query(models.VideoOverlay).filter(models.VideoOverlay.video_id == video_id).all()

def get_overlay(db: Session, overlay_id: int) -> Optional[models.VideoOverlay]:
    return db.query(models.VideoOverlay).filter(models.VideoOverlay.id == overlay_id).first()

# Watermark CRUD operations
def create_watermark(db: Session, watermark_data: schemas.WatermarkCreate, 
                    watermark_path: str) -> models.VideoWatermark:
    db_watermark = models.VideoWatermark(
        video_id=watermark_data.video_id,
        watermark_path=watermark_path,
        x_position=watermark_data.x_position,
        y_position=watermark_data.y_position,
        opacity=watermark_data.opacity,
        scale=watermark_data.scale
    )
    db.add(db_watermark)
    db.commit()
    db.refresh(db_watermark)
    return db_watermark

def get_watermarks_by_video(db: Session, video_id: int) -> List[models.VideoWatermark]:
    return db.query(models.VideoWatermark).filter(models.VideoWatermark.video_id == video_id).all()

def get_watermark(db: Session, watermark_id: int) -> Optional[models.VideoWatermark]:
    return db.query(models.VideoWatermark).filter(models.VideoWatermark.id == watermark_id).first()

# Job CRUD operations - FIXED
def create_processing_job(db: Session, job_type: str, video_id: int, input_data: dict = None) -> models.ProcessingJob:
    job_id = str(uuid.uuid4())
    
    # Convert string to enum using the actual enum values from models
    if isinstance(job_type, str):
        try:
            # Try to find the enum by value (the actual enum values are snake_case)
            job_type_enum = JobType(job_type)
        except ValueError:
            # If direct lookup fails, try common variations
            job_type_mapping = {
                "uploadProcess": "upload_process",
                "textOverlay": "text_overlay", 
                "imageOverlay": "image_overlay",
                "videoOverlay": "video_overlay",
                "qualityConversion": "quality_conversion"
            }
            
            mapped_type = job_type_mapping.get(job_type, job_type)
            try:
                job_type_enum = JobType(mapped_type)
            except ValueError:
                # List valid enum values for error message
                valid_types = [e.value for e in JobType]
                raise ValueError(f"Invalid job_type: {job_type}. Supported types: {valid_types}")
    else:
        job_type_enum = job_type
    
    # FIXED: Use .value to store string values instead of enum objects
    db_job = models.ProcessingJob(
        id=job_id,
        job_type=job_type_enum.value,  # Store string value
        video_id=video_id,
        input_data=json.dumps(input_data) if input_data else None,
        status=JobStatus.PENDING.value  # Store string value
    )
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def get_processing_job(db: Session, job_id: str) -> Optional[models.ProcessingJob]:
    return db.query(models.ProcessingJob).filter(models.ProcessingJob.id == job_id).first()

def update_job_status(db: Session, job_id: str, status: str, result_data: dict = None, error_message: str = None):
    job = db.query(models.ProcessingJob).filter(models.ProcessingJob.id == job_id).first()
    if job:
        # Convert string to enum using the actual enum values
        if isinstance(status, str):
            try:
                status_enum = JobStatus(status)
            except ValueError:
                # List valid enum values for error message
                valid_statuses = [e.value for e in JobStatus]
                raise ValueError(f"Invalid status: {status}. Supported statuses: {valid_statuses}")
        else:
            status_enum = status
            
        # FIXED: Store string value instead of enum object
        job.status = status_enum.value if hasattr(status_enum, 'value') else status
        
        # Update timestamps based on status
        if status_enum == JobStatus.PROCESSING and not job.started_at:
            job.started_at = datetime.utcnow()
        elif status_enum in [JobStatus.COMPLETED, JobStatus.FAILED]:
            job.completed_at = datetime.utcnow()
        
        if result_data:
            job.result_data = json.dumps(result_data)
        if error_message:
            job.error_message = error_message
        
        db.commit()

def get_jobs_by_video(db: Session, video_id: int) -> List[models.ProcessingJob]:
    """Get all jobs for a specific video"""
    return db.query(models.ProcessingJob).filter(
        models.ProcessingJob.video_id == video_id
    ).all()

# Video Variants CRUD operations
def mark_variants_processing(db: Session, video_id: int, qualities: list):
    """Mark video variants as processing by creating placeholder entries"""
    
    quality_dimensions = {
        "1080p": (1920, 1080),
        "720p": (1280, 720),
        "480p": (854, 480),
        "360p": (640, 360)
    }
    
    for quality_str in qualities:
        if quality_str in quality_dimensions:
            width, height = quality_dimensions[quality_str]
            
            # Check if variant already exists - Use string comparison
            existing_variant = db.query(models.VideoVariant).filter(
                models.VideoVariant.original_video_id == video_id,
                models.VideoVariant.quality == quality_str  # Use string directly
            ).first()
            
            if not existing_variant:
                # Create new variant entry - Store string value
                variant = models.VideoVariant(
                    original_video_id=video_id,
                    quality=quality_str,  # Store string value directly
                    filename=f"{quality_str}_{video_id}_processing.mp4",
                    file_path=f"processing/{quality_str}_{video_id}.mp4",
                    width=width,
                    height=height,
                    is_processing=True
                )
                db.add(variant)
            else:
                # Mark existing variant as processing
                existing_variant.is_processing = True
    
    db.commit()

def get_variants_by_video(db: Session, video_id: int) -> List[models.VideoVariant]:
    """Get all variants for a video"""
    return db.query(models.VideoVariant).filter(
        models.VideoVariant.original_video_id == video_id
    ).all()

def get_variant_by_quality(db: Session, video_id: int, quality: str) -> Optional[models.VideoVariant]:
    """Get specific quality variant"""
    return db.query(models.VideoVariant).filter(
        models.VideoVariant.original_video_id == video_id,
        models.VideoVariant.quality == quality  # Use string directly
    ).first()

def create_video_variant(db: Session, original_video_id: int, quality: str, 
                        filename: str, file_path: str, width: int, height: int,
                        file_size: Optional[int] = None, bitrate: Optional[str] = None) -> models.VideoVariant:
    """Create a new video variant"""
    
    # Validate quality is one of the allowed values
    valid_qualities = ["1080p", "720p", "480p", "360p"]
    if quality not in valid_qualities:
        raise ValueError(f"Invalid quality: {quality}. Supported qualities: {valid_qualities}")
    
    variant = models.VideoVariant(
        original_video_id=original_video_id,
        quality=quality,  # Store string value directly
        filename=filename,
        file_path=file_path,
        file_size=file_size,
        width=width,
        height=height,
        bitrate=bitrate,
        is_processing=False
    )
    
    db.add(variant)
    db.commit()
    db.refresh(variant)
    return variant

def update_variant_status(db: Session, variant_id: int, is_processing: bool = False, 
                         file_path: Optional[str] = None, file_size: Optional[int] = None):
    """Update variant processing status"""
    variant = db.query(models.VideoVariant).filter(models.VideoVariant.id == variant_id).first()
    if variant:
        variant.is_processing = is_processing
        if file_path:
            variant.file_path = file_path
        if file_size:
            variant.file_size = file_size
        db.commit()

def update_variant_completed(db: Session, video_id: int, quality: str, 
                           file_path: str, file_size: Optional[int] = None, 
                           bitrate: Optional[str] = None):
    """Update variant when processing is completed"""
    
    variant = db.query(models.VideoVariant).filter(
        models.VideoVariant.original_video_id == video_id,
        models.VideoVariant.quality == quality  # Use string directly
    ).first()
    
    if variant:
        variant.is_processing = False
        variant.file_path = file_path
        if file_size:
            variant.file_size = file_size
        if bitrate:
            variant.bitrate = bitrate
        db.commit()

def delete_variant(db: Session, variant_id: int) -> bool:
    """Delete a video variant"""
    variant = db.query(models.VideoVariant).filter(models.VideoVariant.id == variant_id).first()
    if variant:
        db.delete(variant)
        db.commit()
        return True
    return False

def get_variant_by_id(db: Session, variant_id: int) -> Optional[models.VideoVariant]:
    """Get variant by ID"""
    return db.query(models.VideoVariant).filter(models.VideoVariant.id == variant_id).first()

# Additional utility functions for variants
def get_processing_variants(db: Session, video_id: Optional[int] = None) -> List[models.VideoVariant]:
    """Get all variants that are currently processing"""
    query = db.query(models.VideoVariant).filter(models.VideoVariant.is_processing == True)
    if video_id:
        query = query.filter(models.VideoVariant.original_video_id == video_id)
    return query.all()

def get_completed_variants(db: Session, video_id: int) -> List[models.VideoVariant]:
    """Get all completed variants for a video"""
    return db.query(models.VideoVariant).filter(
        models.VideoVariant.original_video_id == video_id,
        models.VideoVariant.is_processing == False
    ).all()