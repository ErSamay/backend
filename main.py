import os
import uuid
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import shutil
from typing import Optional, List

from database import get_db, engine
from models import Base
import crud
import schemas
from video_service import VideoService

# Celery imports for async processing
from celery_tasks import (
    process_video_upload, trim_video_async, add_overlay_async, 
    add_watermark_async, convert_video_qualities
)
import json

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Video Processing API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directories
UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"
OVERLAYS_DIR = "overlays"
WATERMARKS_DIR = "watermarks"

for directory in [UPLOAD_DIR, PROCESSED_DIR, OVERLAYS_DIR, WATERMARKS_DIR]:
    os.makedirs(directory, exist_ok=True)

@app.get("/")
async def root():
    return {"message": "Video Processing API is running!"}

# Level 1: Upload & Metadata APIs

@app.post("/upload", response_model=schemas.VideoResponse)
async def upload_video(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a video file and extract metadata"""
    
    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get video metadata
        video_info = VideoService.get_video_info(file_path)
        
        # Create video record in database
        video_create = schemas.VideoCreate(
            filename=unique_filename,
            original_filename=file.filename
        )
        
        db_video = crud.create_video(
            db=db,
            video=video_create,
            file_path=file_path,
            duration=video_info.get('duration'),
            file_size=video_info.get('size'),
            width=video_info.get('width'),
            height=video_info.get('height'),
            fps=video_info.get('fps')
        )
        
        return db_video
        
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

@app.get("/videos", response_model=schemas.VideoListResponse)
async def list_videos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all uploaded videos"""
    videos = crud.get_videos(db, skip=skip, limit=limit)
    total = crud.get_videos_count(db)
    
    return schemas.VideoListResponse(videos=videos, total=total)

@app.get("/videos/{video_id}", response_model=schemas.VideoResponse)
async def get_video(video_id: int, db: Session = Depends(get_db)):
    """Get video details by ID"""
    video = crud.get_video(db, video_id=video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@app.get("/videos/{video_id}/download")
async def download_video(video_id: int, db: Session = Depends(get_db)):
    """Download original video file"""
    video = crud.get_video(db, video_id=video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if not os.path.exists(video.file_path):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        video.file_path,
        media_type='application/octet-stream',
        filename=video.original_filename
    )

# Level 2: Trimming API

@app.post("/trim", response_model=schemas.TrimmedVideoResponse)
async def trim_video(
    trim_request: schemas.TrimRequest,
    db: Session = Depends(get_db)
):
    """Trim a video with start and end timestamps"""
    
    # Get original video
    original_video = crud.get_video(db, video_id=trim_request.video_id)
    if original_video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Validate timestamps
    if trim_request.start_time < 0 or trim_request.end_time <= trim_request.start_time:
        raise HTTPException(status_code=400, detail="Invalid timestamps")
    
    if original_video.duration and trim_request.end_time > original_video.duration:
        raise HTTPException(status_code=400, detail="End time exceeds video duration")
    
    # Generate output filename
    file_extension = os.path.splitext(original_video.filename)[1]
    trimmed_filename = f"trimmed_{uuid.uuid4()}{file_extension}"
    output_path = os.path.join(PROCESSED_DIR, trimmed_filename)
    
    try:
        # Trim the video
        success = VideoService.trim_video(
            original_video.file_path,
            output_path,
            trim_request.start_time,
            trim_request.end_time
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to trim video")
        
        # Get file size of trimmed video
        file_size = os.path.getsize(output_path) if os.path.exists(output_path) else None
        duration = trim_request.end_time - trim_request.start_time
        
        # Save trimmed video info to database
        trimmed_video = crud.create_trimmed_video(
            db=db,
            original_video_id=trim_request.video_id,
            filename=trimmed_filename,
            file_path=output_path,
            start_time=trim_request.start_time,
            end_time=trim_request.end_time,
            duration=duration,
            file_size=file_size
        )
        
        return trimmed_video
        
    except Exception as e:
        # Clean up file if operation fails
        if os.path.exists(output_path):
            os.remove(output_path)
        raise HTTPException(status_code=500, detail=f"Error trimming video: {str(e)}")

@app.get("/trimmed/{trimmed_id}/download")
async def download_trimmed_video(trimmed_id: int, db: Session = Depends(get_db)):
    """Download trimmed video file"""
    trimmed_video = crud.get_trimmed_video(db, trimmed_id=trimmed_id)
    if trimmed_video is None:
        raise HTTPException(status_code=404, detail="Trimmed video not found")
    
    if not os.path.exists(trimmed_video.file_path):
        raise HTTPException(status_code=404, detail="Trimmed video file not found")
    
    return FileResponse(
        trimmed_video.file_path,
        media_type='application/octet-stream',
        filename=trimmed_video.filename
    )

# Level 3: Overlays & Watermarking APIs

@app.post("/overlays/text", response_model=schemas.OverlayResponse)
async def add_text_overlay(
    overlay_data: schemas.TextOverlayCreate,
    db: Session = Depends(get_db)
):
    """Add text overlay to video"""
    
    # Get video
    video = crud.get_video(db, video_id=overlay_data.video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Generate output filename
    file_extension = os.path.splitext(video.filename)[1]
    output_filename = f"text_overlay_{uuid.uuid4()}{file_extension}"
    output_path = os.path.join(PROCESSED_DIR, output_filename)
    
    try:
        # Add text overlay
        success = VideoService.add_text_overlay(
            video.file_path,
            output_path,
            overlay_data.content,
            overlay_data.x_position,
            overlay_data.y_position,
            overlay_data.start_time,
            overlay_data.end_time,
            overlay_data.font_size,
            overlay_data.font_color,
            overlay_data.font_family
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add text overlay")
        
        # Update video file path
        video.file_path = output_path
        db.commit()
        
        # Save overlay info to database
        db_overlay = crud.create_text_overlay(db=db, overlay_data=overlay_data)
        
        return db_overlay
        
    except Exception as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        raise HTTPException(status_code=500, detail=f"Error adding text overlay: {str(e)}")

@app.post("/overlays/image", response_model=schemas.OverlayResponse)
async def add_image_overlay(
    video_id: int = Form(...),
    x_position: int = Form(0),
    y_position: int = Form(0),
    start_time: float = Form(0.0),
    end_time: Optional[float] = Form(None),
    overlay_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Add image overlay to video"""
    
    # Get video
    video = crud.get_video(db, video_id=video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Validate overlay file
    if not overlay_file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Overlay file must be an image")
    
    # Save overlay file
    overlay_extension = os.path.splitext(overlay_file.filename)[1]
    overlay_filename = f"overlay_{uuid.uuid4()}{overlay_extension}"
    overlay_path = os.path.join(OVERLAYS_DIR, overlay_filename)
    
    with open(overlay_path, "wb") as buffer:
        shutil.copyfileobj(overlay_file.file, buffer)
    
    # Generate output filename
    file_extension = os.path.splitext(video.filename)[1]
    output_filename = f"image_overlay_{uuid.uuid4()}{file_extension}"
    output_path = os.path.join(PROCESSED_DIR, output_filename)
    
    try:
        # Add image overlay
        success = VideoService.add_image_overlay(
            video.file_path,
            output_path,
            overlay_path,
            x_position,
            y_position,
            start_time,
            end_time
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add image overlay")
        
        # Update video file path
        video.file_path = output_path
        db.commit()
        
        # Create overlay data object
        overlay_data = schemas.ImageOverlayCreate(
            video_id=video_id,
            x_position=x_position,
            y_position=y_position,
            start_time=start_time,
            end_time=end_time
        )
        
        # Save overlay info to database
        db_overlay = crud.create_file_overlay(
            db=db, 
            overlay_data=overlay_data, 
            file_path=overlay_path,
            overlay_type="image"
        )
        
        return db_overlay
        
    except Exception as e:
        # Clean up files
        if os.path.exists(output_path):
            os.remove(output_path)
        if os.path.exists(overlay_path):
            os.remove(overlay_path)
        raise HTTPException(status_code=500, detail=f"Error adding image overlay: {str(e)}")

@app.post("/overlays/video", response_model=schemas.OverlayResponse)
async def add_video_overlay(
    video_id: int = Form(...),
    x_position: int = Form(0),
    y_position: int = Form(0),
    start_time: float = Form(0.0),
    end_time: Optional[float] = Form(None),
    overlay_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Add video overlay to video"""
    
    # Get video
    video = crud.get_video(db, video_id=video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Validate overlay file
    if not overlay_file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="Overlay file must be a video")
    
    # Save overlay file
    overlay_extension = os.path.splitext(overlay_file.filename)[1]
    overlay_filename = f"video_overlay_{uuid.uuid4()}{overlay_extension}"
    overlay_path = os.path.join(OVERLAYS_DIR, overlay_filename)
    
    with open(overlay_path, "wb") as buffer:
        shutil.copyfileobj(overlay_file.file, buffer)
    
    # Generate output filename
    file_extension = os.path.splitext(video.filename)[1]
    output_filename = f"video_overlay_{uuid.uuid4()}{file_extension}"
    output_path = os.path.join(PROCESSED_DIR, output_filename)
    
    try:
        # Add video overlay
        success = VideoService.add_video_overlay(
            video.file_path,
            output_path,
            overlay_path,
            x_position,
            y_position,
            start_time,
            end_time
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add video overlay")
        
        # Update video file path
        video.file_path = output_path
        db.commit()
        
        # Create overlay data object
        overlay_data = schemas.VideoOverlayCreate(
            video_id=video_id,
            x_position=x_position,
            y_position=y_position,
            start_time=start_time,
            end_time=end_time
        )
        
        # Save overlay info to database
        db_overlay = crud.create_file_overlay(
            db=db, 
            overlay_data=overlay_data, 
            file_path=overlay_path,
            overlay_type="video"
        )
        
        return db_overlay
        
    except Exception as e:
        # Clean up files
        if os.path.exists(output_path):
            os.remove(output_path)
        if os.path.exists(overlay_path):
            os.remove(overlay_path)
        raise HTTPException(status_code=500, detail=f"Error adding video overlay: {str(e)}")

@app.post("/watermark", response_model=schemas.WatermarkResponse)
async def add_watermark(
    video_id: int = Form(...),
    x_position: int = Form(10),
    y_position: int = Form(10),
    opacity: float = Form(1.0),
    scale: float = Form(1.0),
    watermark_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Add watermark to video"""
    
    # Get video
    video = crud.get_video(db, video_id=video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Validate watermark file
    if not watermark_file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Watermark file must be an image")
    
    # Save watermark file
    watermark_extension = os.path.splitext(watermark_file.filename)[1]
    watermark_filename = f"watermark_{uuid.uuid4()}{watermark_extension}"
    watermark_path = os.path.join(WATERMARKS_DIR, watermark_filename)
    
    with open(watermark_path, "wb") as buffer:
        shutil.copyfileobj(watermark_file.file, buffer)
    
    # Generate output filename
    file_extension = os.path.splitext(video.filename)[1]
    output_filename = f"watermarked_{uuid.uuid4()}{file_extension}"
    output_path = os.path.join(PROCESSED_DIR, output_filename)
    
    try:
        # Add watermark
        success = VideoService.add_watermark(
            video.file_path,
            output_path,
            watermark_path,
            x_position,
            y_position,
            opacity,
            scale
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add watermark")
        
        # Update video file path
        video.file_path = output_path
        db.commit()
        
        # Create watermark data object
        watermark_data = schemas.WatermarkCreate(
            video_id=video_id,
            x_position=x_position,
            y_position=y_position,
            opacity=opacity,
            scale=scale
        )
        
        # Save watermark info to database
        db_watermark = crud.create_watermark(
            db=db, 
            watermark_data=watermark_data, 
            watermark_path=watermark_path
        )
        
        return db_watermark
        
    except Exception as e:
        # Clean up files
        if os.path.exists(output_path):
            os.remove(output_path)
        if os.path.exists(watermark_path):
            os.remove(watermark_path)
        raise HTTPException(status_code=500, detail=f"Error adding watermark: {str(e)}")

# =================== LEVEL 4: ASYNC JOB QUEUE ENDPOINTS ===================

@app.post("/async/upload", response_model=dict)
async def upload_video_async(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a video file and process asynchronously"""
    
    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    try:
        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create video record in database
        video_create = schemas.VideoCreate(
            filename=unique_filename,
            original_filename=file.filename
        )
        
        db_video = crud.create_video(
            db=db,
            video=video_create,
            file_path=file_path
        )
        
        # Create processing job
        job = crud.create_processing_job(
            db=db,
            job_type="upload_process",
            video_id=db_video.id,
            input_data={"file_path": file_path}
        )
        
        # Start async processing
        process_video_upload.apply_async(
            args=[db_video.id, file_path],
            task_id=job.id
        )
        
        return {
            "job_id": job.id,
            "video_id": db_video.id,
            "message": "Video uploaded successfully, processing started"
        }
        
    except Exception as e:
        # Clean up file if database operation fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error uploading video: {str(e)}")

@app.post("/async/trim", response_model=dict)
async def trim_video_async_endpoint(
    trim_request: schemas.AsyncTrimRequest,
    db: Session = Depends(get_db)
):
    """Trim a video asynchronously"""
    
    # Validate video exists
    original_video = crud.get_video(db, video_id=trim_request.video_id)
    if original_video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Validate timestamps
    if trim_request.start_time < 0 or trim_request.end_time <= trim_request.start_time:
        raise HTTPException(status_code=400, detail="Invalid timestamps")
    
    if original_video.duration and trim_request.end_time > original_video.duration:
        raise HTTPException(status_code=400, detail="End time exceeds video duration")
    
    # Create processing job
    job_data = {
        "video_id": trim_request.video_id,
        "start_time": trim_request.start_time,
        "end_time": trim_request.end_time
    }
    
    job = crud.create_processing_job(
        db=db,
        job_type="trim",
        video_id=trim_request.video_id,
        input_data=job_data
    )
    
    # Start async processing
    trim_video_async.apply_async(
        args=[job_data],
        task_id=job.id
    )
    
    return {
        "job_id": job.id,
        "message": "Video trim job started"
    }

@app.post("/async/overlays/text", response_model=dict)
async def add_text_overlay_async_endpoint(
    overlay_data: schemas.AsyncTextOverlayCreate,
    db: Session = Depends(get_db)
):
    """Add text overlay to video asynchronously"""
    
    # Validate video exists
    video = crud.get_video(db, video_id=overlay_data.video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Prepare job data
    job_data = {
        "overlay_type": "text",
        "video_id": overlay_data.video_id,
        "content": overlay_data.content,
        "x_position": overlay_data.x_position,
        "y_position": overlay_data.y_position,
        "start_time": overlay_data.start_time,
        "end_time": overlay_data.end_time,
        "font_size": overlay_data.font_size,
        "font_color": overlay_data.font_color,
        "font_family": overlay_data.font_family
    }
    
    # Create processing job
    job = crud.create_processing_job(
        db=db,
        job_type="text_overlay",
        video_id=overlay_data.video_id,
        input_data=job_data
    )
    
    # Start async processing
    add_overlay_async.apply_async(
        args=[job_data],
        task_id=job.id
    )
    
    return {
        "job_id": job.id,
        "message": "Text overlay job started"
    }

@app.post("/async/overlays/image", response_model=dict)
async def add_image_overlay_async_endpoint(
    video_id: int = Form(...),
    x_position: int = Form(0),
    y_position: int = Form(0),
    start_time: float = Form(0.0),
    end_time: Optional[float] = Form(None),
    overlay_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Add image overlay to video asynchronously"""
    
    # Validate video exists
    video = crud.get_video(db, video_id=video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Validate overlay file
    if not overlay_file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Overlay file must be an image")
    
    # Save overlay file
    overlay_extension = os.path.splitext(overlay_file.filename)[1]
    overlay_filename = f"overlay_{uuid.uuid4()}{overlay_extension}"
    overlay_path = os.path.join(OVERLAYS_DIR, overlay_filename)
    
    with open(overlay_path, "wb") as buffer:
        shutil.copyfileobj(overlay_file.file, buffer)
    
    # Prepare job data
    job_data = {
        "overlay_type": "image",
        "video_id": video_id,
        "overlay_file_path": overlay_path,
        "x_position": x_position,
        "y_position": y_position,
        "start_time": start_time,
        "end_time": end_time
    }
    
    # Create processing job
    job = crud.create_processing_job(
        db=db,
        job_type="image_overlay",
        video_id=video_id,
        input_data=job_data
    )
    
    # Start async processing
    add_overlay_async.apply_async(
        args=[job_data],
        task_id=job.id
    )
    
    return {
        "job_id": job.id,
        "message": "Image overlay job started"
    }

@app.post("/async/watermark", response_model=dict)
async def add_watermark_async_endpoint(
    video_id: int = Form(...),
    x_position: int = Form(10),
    y_position: int = Form(10),
    opacity: float = Form(1.0),
    scale: float = Form(1.0),
    watermark_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Add watermark to video asynchronously"""
    
    # Validate video exists
    video = crud.get_video(db, video_id=video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Validate watermark file
    if not watermark_file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Watermark file must be an image")
    
    # Save watermark file
    watermark_extension = os.path.splitext(watermark_file.filename)[1]
    watermark_filename = f"watermark_{uuid.uuid4()}{watermark_extension}"
    watermark_path = os.path.join(WATERMARKS_DIR, watermark_filename)
    
    with open(watermark_path, "wb") as buffer:
        shutil.copyfileobj(watermark_file.file, buffer)
    
    # Prepare job data
    job_data = {
        "video_id": video_id,
        "watermark_path": watermark_path,
        "x_position": x_position,
        "y_position": y_position,
        "opacity": opacity,
        "scale": scale
    }
    
    # Create processing job
    job = crud.create_processing_job(
        db=db,
        job_type="watermark",
        video_id=video_id,
        input_data=job_data
    )
    
    # Start async processing
    add_watermark_async.apply_async(
        args=[job_data],
        task_id=job.id
    )
    
    return {
        "job_id": job.id,
        "message": "Watermark job started"
    }

@app.get("/status/{job_id}", response_model=schemas.JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get job status"""
    
    job = crud.get_processing_job(db, job_id=job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Calculate progress percentage based on job type and status
    progress_percentage = None
    message = None
    
    if job.status == "pending":
        progress_percentage = 0
        message = "Job is waiting to be processed"
    elif job.status == "processing":
        progress_percentage = 50
        message = "Job is currently being processed"
    elif job.status == "completed":
        progress_percentage = 100
        message = "Job completed successfully"
    elif job.status == "failed":
        progress_percentage = 0
        message = f"Job failed: {job.error_message}"
    
    return schemas.JobStatusResponse(
        job_id=job_id,
        status=job.status,
        progress_percentage=progress_percentage,
        message=message
    )

@app.get("/result/{job_id}")
async def get_job_result(job_id: str, db: Session = Depends(get_db)):
    """Get job result or download processed file"""
    
    job = crud.get_processing_job(db, job_id=job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != "completed":
        return {
            "job_id": job_id,
            "status": job.status,
            "message": "Job not completed yet" if job.status in ["pending", "processing"] else f"Job failed: {job.error_message}"
        }
    
    # Parse result data
    result_data = json.loads(job.result_data) if job.result_data else {}
    
    # For trim jobs, return download link for trimmed video
    if job.job_type == "trim" and "trimmed_video_id" in result_data:
        trimmed_video = crud.get_trimmed_video(db, result_data["trimmed_video_id"])
        if trimmed_video and os.path.exists(trimmed_video.file_path):
            return FileResponse(
                trimmed_video.file_path,
                media_type='application/octet-stream',
                filename=trimmed_video.filename
            )
    
    # For other jobs, return the processed video
    elif "output_file" in result_data:
        output_path = os.path.join("processed", result_data["output_file"])
        if os.path.exists(output_path):
            return FileResponse(
                output_path,
                media_type='application/octet-stream',
                filename=result_data["output_file"]
            )
    
    # If no file to download, return result data
    return {
        "job_id": job_id,
        "status": job.status,
        "result": result_data
    }

# =================== LEVEL 5: MULTIPLE OUTPUT QUALITIES ===================

@app.post("/qualities/convert", response_model=dict)
async def convert_video_qualities_endpoint(
    quality_request: schemas.QualityRequest,
    db: Session = Depends(get_db)
):
    """Convert video to multiple qualities asynchronously"""
    
    # Validate video exists
    video = crud.get_video(db, video_id=quality_request.video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Mark variants as processing
    qualities_list = [q.value for q in quality_request.qualities]
    crud.mark_variants_processing(db, quality_request.video_id, qualities_list)
    
    # Prepare job data
    job_data = {
        "video_id": quality_request.video_id,
        "qualities": qualities_list
    }
    
    # Create processing job
    job = crud.create_processing_job(
        db=db,
        job_type="quality_conversion",
        video_id=quality_request.video_id,
        input_data=job_data
    )
    
    # Start async processing
    convert_video_qualities.apply_async(
        args=[job_data],
        task_id=job.id
    )
    
    return {
        "job_id": job.id,
        "message": f"Quality conversion started for {len(qualities_list)} variants",
        "qualities": qualities_list
    }

@app.get("/videos/{video_id}/qualities", response_model=List[schemas.VideoVariantResponse])
async def get_video_qualities(video_id: int, db: Session = Depends(get_db)):
    """Get all quality variants of a video"""
    
    # Validate video exists
    video = crud.get_video(db, video_id=video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    variants = crud.get_variants_by_video(db, video_id=video_id)
    return variants

@app.get("/videos/{video_id}/qualities/{quality}")
async def download_video_quality(
    video_id: int, 
    quality: schemas.VideoQualityEnum,
    db: Session = Depends(get_db)
):
    """Download specific quality version of video"""
    
    # Validate video exists
    video = crud.get_video(db, video_id=video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Get variant
    variant = crud.get_variant_by_quality(db, video_id, quality.value)
    if variant is None:
        raise HTTPException(status_code=404, detail=f"Quality {quality.value} not found for this video")
    
    if variant.is_processing:
        raise HTTPException(status_code=202, detail=f"Quality {quality.value} is still being processed")
    
    if not os.path.exists(variant.file_path):
        raise HTTPException(status_code=404, detail="Quality file not found")
    
    return FileResponse(
        variant.file_path,
        media_type='application/octet-stream',
        filename=f"{quality.value}_{video.original_filename}"
    )

@app.get("/videos/{video_id}/qualities/{quality}/info", response_model=schemas.VideoVariantResponse)
async def get_video_quality_info(
    video_id: int, 
    quality: schemas.VideoQualityEnum,
    db: Session = Depends(get_db)
):
    """Get information about specific quality variant"""
    
    # Validate video exists
    video = crud.get_video(db, video_id=video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Get variant
    variant = crud.get_variant_by_quality(db, video_id, quality.value)
    if variant is None:
        raise HTTPException(status_code=404, detail=f"Quality {quality.value} not found for this video")
    
    return variant

# Additional utility endpoints
@app.get("/jobs/{video_id}", response_model=List[schemas.JobResponse])
async def get_video_jobs(video_id: int, db: Session = Depends(get_db)):
    """Get all jobs for a specific video"""
    
    # Validate video exists
    video = crud.get_video(db, video_id=video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    jobs = crud.get_jobs_by_video(db, video_id=video_id)
    
    # Parse result_data for each job
    job_responses = []
    for job in jobs:
        result_data = json.loads(job.result_data) if job.result_data else None
        
        job_response = schemas.JobResponse(
            job_id=job.id,
            job_type=job.job_type,
            status=job.status,
            video_id=job.video_id,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message,
            result_data=result_data
        )
        job_responses.append(job_response)
    
    return job_responses

# Additional utility endpoints

@app.get("/videos/{video_id}/overlays", response_model=List[schemas.OverlayResponse])
async def get_video_overlays(video_id: int, db: Session = Depends(get_db)):
    """Get all overlays for a video"""
    video = crud.get_video(db, video_id=video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    overlays = crud.get_overlays_by_video(db, video_id=video_id)
    return overlays

@app.get("/videos/{video_id}/watermarks", response_model=List[schemas.WatermarkResponse])
async def get_video_watermarks(video_id: int, db: Session = Depends(get_db)):
    """Get all watermarks for a video"""
    video = crud.get_video(db, video_id=video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    watermarks = crud.get_watermarks_by_video(db, video_id=video_id)
    return watermarks

@app.get("/videos/{video_id}/trimmed", response_model=List[schemas.TrimmedVideoResponse])
async def get_trimmed_videos(video_id: int, db: Session = Depends(get_db)):
    """Get all trimmed versions of a video"""
    video = crud.get_video(db, video_id=video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    
    trimmed_videos = crud.get_trimmed_videos_by_original(db, original_video_id=video_id)
    return trimmed_videos

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)