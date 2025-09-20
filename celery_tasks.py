from celery import current_task
from celery_config import celery_app
from database import SessionLocal
import crud
import models
import json
import uuid
import os
from video_service import VideoService
from datetime import datetime
import shutil

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        pass

def update_job_status(db, job_id: str, status: str, result_data=None, error_message=None):
    """Update job status in database"""
    job = db.query(models.ProcessingJob).filter(models.ProcessingJob.id == job_id).first()
    if job:
        job.status = status
        if status == "processing" and not job.started_at:
            job.started_at = datetime.utcnow()
        elif status in ["completed", "failed"]:
            job.completed_at = datetime.utcnow()
        
        if result_data:
            job.result_data = json.dumps(result_data)
        if error_message:
            job.error_message = error_message
        
        db.commit()

@celery_app.task(bind=True)
def process_video_upload(self, video_id: int, file_path: str):
    """Process uploaded video asynchronously"""
    db = get_db()
    job_id = self.request.id
    
    try:
        update_job_status(db, job_id, "processing")
        
        # Get video info
        video_info = VideoService.get_video_info(file_path)
        
        # Update video record
        video = crud.get_video(db, video_id)
        if video:
            video.duration = video_info.get('duration')
            video.file_size = video_info.get('size')
            video.width = video_info.get('width')
            video.height = video_info.get('height')
            video.fps = video_info.get('fps')
            video.is_processed = True
            db.commit()
        
        result_data = {
            "video_id": video_id,
            "metadata": video_info,
            "status": "completed"
        }
        
        update_job_status(db, job_id, "completed", result_data)
        return result_data
        
    except Exception as e:
        update_job_status(db, job_id, "failed", error_message=str(e))
        raise
    finally:
        db.close()

@celery_app.task(bind=True)
def trim_video_async(self, job_data: dict):
    """Trim video asynchronously"""
    db = get_db()
    job_id = self.request.id
    
    try:
        update_job_status(db, job_id, "processing")
        
        video_id = job_data['video_id']
        start_time = job_data['start_time']
        end_time = job_data['end_time']
        
        # Get original video
        original_video = crud.get_video(db, video_id)
        if not original_video:
            raise ValueError("Video not found")
        
        # Generate output filename
        file_extension = os.path.splitext(original_video.filename)[1]
        trimmed_filename = f"trimmed_{uuid.uuid4()}{file_extension}"
        output_path = os.path.join("processed", trimmed_filename)
        
        # Trim the video
        success = VideoService.trim_video(
            original_video.file_path,
            output_path,
            start_time,
            end_time
        )
        
        if not success:
            raise ValueError("Failed to trim video")
        
        # Save trimmed video info
        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else None
        duration = end_time - start_time
        
        trimmed_video = crud.create_trimmed_video(
            db=db,
            original_video_id=video_id,
            filename=trimmed_filename,
            file_path=output_path,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            file_size=file_size
        )
        
        result_data = {
            "trimmed_video_id": trimmed_video.id,
            "filename": trimmed_filename,
            "file_path": output_path,
            "duration": duration
        }
        
        update_job_status(db, job_id, "completed", result_data)
        return result_data
        
    except Exception as e:
        update_job_status(db, job_id, "failed", error_message=str(e))
        raise
    finally:
        db.close()

@celery_app.task(bind=True)
def add_overlay_async(self, job_data: dict):
    """Add overlay to video asynchronously"""
    db = get_db()
    job_id = self.request.id
    
    try:
        update_job_status(db, job_id, "processing")
        
        overlay_type = job_data['overlay_type']
        video_id = job_data['video_id']
        
        # Get video
        video = crud.get_video(db, video_id)
        if not video:
            raise ValueError("Video not found")
        
        # Generate output filename
        file_extension = os.path.splitext(video.filename)[1]
        output_filename = f"{overlay_type}_overlay_{uuid.uuid4()}{file_extension}"
        output_path = os.path.join("processed", output_filename)
        
        success = False
        db_overlay = None
        
        if overlay_type == "text":
            success = VideoService.add_text_overlay(
                video.file_path,
                output_path,
                job_data['content'],
                job_data['x_position'],
                job_data['y_position'],
                job_data['start_time'],
                job_data.get('end_time'),
                job_data.get('font_size', 24),
                job_data.get('font_color', 'white'),
                job_data.get('font_family', 'Arial')
            )
            
            if success:
                # Create text overlay record
                overlay_data = {
                    'video_id': video_id,
                    'overlay_type': 'text',
                    'content': job_data['content'],
                    'x_position': job_data['x_position'],
                    'y_position': job_data['y_position'],
                    'start_time': job_data['start_time'],
                    'end_time': job_data.get('end_time'),
                    'font_size': job_data.get('font_size', 24),
                    'font_color': job_data.get('font_color', 'white'),
                    'font_family': job_data.get('font_family', 'Arial')
                }
                
                db_overlay = models.VideoOverlay(**overlay_data)
                db.add(db_overlay)
                db.commit()
                db.refresh(db_overlay)
        
        elif overlay_type in ["image", "video"]:
            success = VideoService.add_image_overlay(
                video.file_path,
                output_path,
                job_data['overlay_file_path'],
                job_data['x_position'],
                job_data['y_position'],
                job_data['start_time'],
                job_data.get('end_time')
            )
            
            if success:
                overlay_data = {
                    'video_id': video_id,
                    'overlay_type': overlay_type,
                    'file_path': job_data['overlay_file_path'],
                    'x_position': job_data['x_position'],
                    'y_position': job_data['y_position'],
                    'start_time': job_data['start_time'],
                    'end_time': job_data.get('end_time')
                }
                
                db_overlay = models.VideoOverlay(**overlay_data)
                db.add(db_overlay)
                db.commit()
                db.refresh(db_overlay)
        
        if not success:
            raise ValueError(f"Failed to add {overlay_type} overlay")
        
        # Update video file path
        video.file_path = output_path
        db.commit()
        
        result_data = {
            "overlay_id": db_overlay.id if db_overlay else None,
            "output_file": output_filename,
            "overlay_type": overlay_type
        }
        
        update_job_status(db, job_id, "completed", result_data)
        return result_data
        
    except Exception as e:
        update_job_status(db, job_id, "failed", error_message=str(e))
        raise
    finally:
        db.close()

@celery_app.task(bind=True)
def add_watermark_async(self, job_data: dict):
    """Add watermark to video asynchronously"""
    db = get_db()
    job_id = self.request.id
    
    try:
        update_job_status(db, job_id, "processing")
        
        video_id = job_data['video_id']
        
        # Get video
        video = crud.get_video(db, video_id)
        if not video:
            raise ValueError("Video not found")
        
        # Generate output filename
        file_extension = os.path.splitext(video.filename)[1]
        output_filename = f"watermarked_{uuid.uuid4()}{file_extension}"
        output_path = os.path.join("processed", output_filename)
        
        # Add watermark
        success = VideoService.add_watermark(
            video.file_path,
            output_path,
            job_data['watermark_path'],
            job_data.get('x_position', 10),
            job_data.get('y_position', 10),
            job_data.get('opacity', 1.0),
            job_data.get('scale', 1.0)
        )
        
        if not success:
            raise ValueError("Failed to add watermark")
        
        # Update video file path
        video.file_path = output_path
        db.commit()
        
        # Save watermark info
        watermark_data = {
            'video_id': video_id,
            'watermark_path': job_data['watermark_path'],
            'x_position': job_data.get('x_position', 10),
            'y_position': job_data.get('y_position', 10),
            'opacity': job_data.get('opacity', 1.0),
            'scale': job_data.get('scale', 1.0)
        }
        
        db_watermark = models.VideoWatermark(**watermark_data)
        db.add(db_watermark)
        db.commit()
        db.refresh(db_watermark)
        
        result_data = {
            "watermark_id": db_watermark.id,
            "output_file": output_filename
        }
        
        update_job_status(db, job_id, "completed", result_data)
        return result_data
        
    except Exception as e:
        update_job_status(db, job_id, "failed", error_message=str(e))
        raise
    finally:
        db.close()

@celery_app.task(bind=True)
def convert_video_qualities(self, job_data: dict):
    """Convert video to multiple qualities"""
    db = get_db()
    job_id = self.request.id
    
    try:
        update_job_status(db, job_id, "processing")
        
        video_id = job_data['video_id']
        qualities = job_data['qualities']
        
        # Get original video
        video = crud.get_video(db, video_id)
        if not video:
            raise ValueError("Video not found")
        
        results = []
        
        for quality in qualities:
            try:
                # Generate filename
                file_extension = os.path.splitext(video.filename)[1]
                quality_filename = f"{quality}_{uuid.uuid4()}{file_extension}"
                quality_path = os.path.join("processed", quality_filename)
                
                # Get quality settings
                width, height, bitrate = get_quality_settings(quality)
                
                # Convert video
                success = VideoService.convert_video_quality(
                    video.file_path,
                    quality_path,
                    width,
                    height,
                    bitrate
                )
                
                if success:
                    # Get file size
                    file_size = os.path.getsize(quality_path) if os.path.exists(quality_path) else None
                    
                    # Save variant to database
                    variant_data = {
                        'original_video_id': video_id,
                        'quality': quality,
                        'filename': quality_filename,
                        'file_path': quality_path,
                        'file_size': file_size,
                        'width': width,
                        'height': height,
                        'bitrate': bitrate,
                        'is_processing': False
                    }
                    
                    db_variant = models.VideoVariant(**variant_data)
                    db.add(db_variant)
                    db.commit()
                    db.refresh(db_variant)
                    
                    results.append({
                        'quality': quality,
                        'variant_id': db_variant.id,
                        'filename': quality_filename,
                        'success': True
                    })
                else:
                    results.append({
                        'quality': quality,
                        'success': False,
                        'error': 'Conversion failed'
                    })
                    
            except Exception as e:
                results.append({
                    'quality': quality,
                    'success': False,
                    'error': str(e)
                })
        
        result_data = {
            "video_id": video_id,
            "conversions": results,
            "total_successful": sum(1 for r in results if r.get('success'))
        }
        
        update_job_status(db, job_id, "completed", result_data)
        return result_data
        
    except Exception as e:
        update_job_status(db, job_id, "failed", error_message=str(e))
        raise
    finally:
        db.close()

def get_quality_settings(quality: str):
    """Get video quality settings"""
    settings = {
        "1080p": (1920, 1080, "5000k"),
        "720p": (1280, 720, "3000k"),
        "480p": (854, 480, "1500k"),
        "360p": (640, 360, "800k")
    }
    return settings.get(quality, (1280, 720, "3000k"))