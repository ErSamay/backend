from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class OverlayType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"

class JobStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobTypeEnum(str, Enum):
    UPLOAD_PROCESS = "upload_process"
    TRIM = "trim"
    TEXT_OVERLAY = "text_overlay"
    IMAGE_OVERLAY = "image_overlay"
    VIDEO_OVERLAY = "video_overlay"
    WATERMARK = "watermark"
    QUALITY_CONVERSION = "quality_conversion"

class VideoQualityEnum(str, Enum):
    Q_1080P = "1080p"
    Q_720P = "720p"
    Q_480P = "480p"
    Q_360P = "360p"

# Video schemas
class VideoBase(BaseModel):
    filename: str
    original_filename: str

class VideoCreate(VideoBase):
    pass

class VideoResponse(VideoBase):
    id: int
    duration: Optional[float]
    file_size: Optional[int]
    width: Optional[int]
    height: Optional[int]
    fps: Optional[float]
    upload_time: datetime
    file_path: str
    is_processed: bool
    
    class Config:
        from_attributes = True

# Trim schemas
class TrimRequest(BaseModel):
    video_id: int
    start_time: float
    end_time: float

class TrimmedVideoResponse(BaseModel):
    id: int
    original_video_id: int
    filename: str
    start_time: float
    end_time: float
    duration: float
    file_size: Optional[int]
    file_path: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Overlay schemas
class OverlayBase(BaseModel):
    overlay_type: OverlayType
    x_position: int = 0
    y_position: int = 0
    start_time: float = 0.0
    end_time: Optional[float] = None

class TextOverlayCreate(OverlayBase):
    video_id: int
    overlay_type: OverlayType = OverlayType.TEXT
    content: str
    font_size: int = 24
    font_color: str = "white"
    font_family: str = "Arial"

class ImageOverlayCreate(OverlayBase):
    video_id: int
    overlay_type: OverlayType = OverlayType.IMAGE

class VideoOverlayCreate(OverlayBase):
    video_id: int
    overlay_type: OverlayType = OverlayType.VIDEO

class OverlayResponse(BaseModel):
    id: int
    video_id: int
    overlay_type: str
    content: Optional[str]
    file_path: Optional[str]
    x_position: int
    y_position: int
    start_time: float
    end_time: Optional[float]
    font_size: Optional[int]
    font_color: Optional[str]
    font_family: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# Watermark schemas
class WatermarkCreate(BaseModel):
    video_id: int
    x_position: int = 10
    y_position: int = 10
    opacity: float = 1.0
    scale: float = 1.0

class WatermarkResponse(BaseModel):
    id: int
    video_id: int
    watermark_path: str
    x_position: int
    y_position: int
    opacity: float
    scale: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# Job schemas
class JobResponse(BaseModel):
    job_id: str
    job_type: JobTypeEnum
    status: JobStatusEnum
    video_id: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result_data: Optional[dict] = None
    
    class Config:
        from_attributes = True

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatusEnum
    progress_percentage: Optional[int] = None
    message: Optional[str] = None

# Video quality schemas
class QualityRequest(BaseModel):
    video_id: int
    qualities: List[VideoQualityEnum]

class VideoVariantResponse(BaseModel):
    id: int
    original_video_id: int
    quality: VideoQualityEnum
    filename: str
    file_size: Optional[int]
    width: int
    height: int
    bitrate: Optional[str]
    is_processing: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Async request schemas
class AsyncTrimRequest(TrimRequest):
    pass

class AsyncTextOverlayCreate(TextOverlayCreate):
    pass

class AsyncWatermarkCreate(WatermarkCreate):
    pass

# Response schemas
class VideoListResponse(BaseModel):
    videos: List[VideoResponse]
    total: int