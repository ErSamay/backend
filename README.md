# 🎬 Video Processing API - Complete Backend

A comprehensive FastAPI backend for video editing operations with async processing and multiple quality outputs. Built with FastAPI, PostgreSQL, Redis, Celery, and FFmpeg.

## 🚀 Features Overview

### ✅ **Level 1 - Upload & Metadata**
- Video upload with automatic metadata extraction
- Database storage of video information
- List all uploaded videos
- Download original videos

### ✅ **Level 2 - Video Trimming** 
- Trim videos with start/end timestamps
- Download trimmed videos
- Track trimmed video history

### ✅ **Level 3 - Overlays & Watermarking**
- Text overlays with positioning and timing (supports Indian languages)
- Image overlays with positioning and timing
- Video overlays with positioning and timing
- Watermark addition with opacity and scaling

### ✅ **Level 4 - Async Job Queue**
- Background processing with Celery + Redis
- Immediate job_id response for all operations
- Real-time job status tracking
- Download processed results

### ✅ **Level 5 - Multiple Output Qualities**
- Generate multiple video qualities (1080p, 720p, 480p, 360p)
- Download specific quality versions
- Quality information API
- Async quality conversion processing

## 🏗️ Project Structure

```
backend/
├── main.py                           # FastAPI application with all endpoints
├── database.py                       # PostgreSQL database connection
├── models.py                         # SQLAlchemy models (all tables)
├── schemas.py                        # Pydantic schemas for validation
├── crud.py                          # Database operations (CRUD)
├── video_service.py                 # FFmpeg video processing service
├── celery_config.py                 # Celery configuration
├── celery_tasks.py                  # Async task definitions
├── start_celery.py                  # Celery startup script
├── setup.py                         # Automated setup script
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── .env                            # Your environment configuration
├── alembic.ini                     # Alembic configuration
├── alembic/                        # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       
├── uploads/                        # Original uploaded videos
├── processed/                      # Processed videos (trimmed, overlays, etc.)
├── overlays/                       # Overlay media files (images/videos)
├── watermarks/                     # Watermark image files
├── README.md                       # This comprehensive guide
└── LEVEL_4_5_SETUP_GUIDE.md       # Advanced features setup guide
```

## 📋 Prerequisites

### **Required Software:**
- **Python 3.8+** 
- **PostgreSQL 12+** (running and accessible)
- **Redis 6+** (for async job processing)
- **FFmpeg 4.0+** (for video processing)

### **Installation Commands:**

#### **Ubuntu/Debian:**
```bash
# System dependencies
sudo apt update
sudo apt install python3 python3-pip postgresql postgresql-contrib redis-server ffmpeg

# Start services
sudo systemctl start postgresql
sudo systemctl start redis-server
sudo systemctl enable postgresql
sudo systemctl enable redis-server
```

#### **macOS:**
```bash
# Using Homebrew
brew install python postgresql redis ffmpeg
brew services start postgresql
brew services start redis
```

#### **Windows:**
- Install Python from [python.org](https://python.org)
- Install PostgreSQL from [postgresql.org](https://postgresql.org)
- Install Redis from [redis.io](https://redis.io/downloads) or use Docker
- Install FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)

## 🛠️ Quick Setup (Automated)

### **Method 1: One-Command Setup**
```bash
# Clone repository
git clone <your-repo-url>
cd backend

# Run automated setup
python setup.py

# Configure environment (edit with your database credentials)
cp .env.example .env
nano .env

# Run migrations
alembic upgrade head

# You're ready to start!
```

## 🔧 Manual Setup (Step by Step)

### **Step 1: Install Dependencies**
```bash
pip install -r requirements.txt
```

### **Step 2: Database Setup**
```bash
# Create PostgreSQL database
createdb videoprocessing

# Or using psql
psql -U postgres
CREATE DATABASE videoprocessing;
\q
```

### **Step 3: Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

**Configure your `.env` file:**
```bash
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/videoprocessing

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### **Step 4: Database Migration**
```bash
# Initialize migrations (if needed)
alembic init alembic

# Run migrations
alembic upgrade head
```

### **Step 5: Create Directories**
```bash
mkdir -p uploads processed overlays watermarks
```

## 🚀 Starting the Application

You need to run **3 separate terminals** for full functionality:

### **Terminal 1: Redis Server** (if not running as service)
```bash
redis-server
```

### **Terminal 2: Celery Worker** (for async processing)
```bash
python start_celery.py
```

### **Terminal 3: FastAPI Server**
```bash
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### **Optional Terminal 4: Flower Monitoring**
```bash
python start_celery.py flower
```
Visit http://localhost:5555 for job monitoring dashboard

## 📚 API Documentation

### **Interactive Documentation:**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### **Base URL:** `http://localhost:8000`

## 🎯 Complete API Reference

### **Basic Video Operations**

#### **Upload Video**
```bash
POST /upload
curl -X POST "http://localhost:8000/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@video.mp4"
```

#### **List Videos**
```bash
GET /videos
curl "http://localhost:8000/videos?skip=0&limit=10"
```

#### **Get Video Details**
```bash
GET /videos/{video_id}
curl "http://localhost:8000/videos/1"
```

#### **Download Video**
```bash
GET /videos/{video_id}/download
curl "http://localhost:8000/videos/1/download" -o "video.mp4"
```

### **Video Trimming**

#### **Synchronous Trim**
```bash
POST /trim
curl -X POST "http://localhost:8000/trim" \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": 1,
    "start_time": 10.0,
    "end_time": 30.0
  }'
```

#### **Download Trimmed Video**
```bash
GET /trimmed/{trimmed_id}/download
curl "http://localhost:8000/trimmed/1/download" -o "trimmed.mp4"
```

### **Overlays & Watermarks**

#### **Add Text Overlay**
```bash
POST /overlays/text
curl -X POST "http://localhost:8000/overlays/text" \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": 1,
    "content": "Hello World! नमस्ते दुनिया!",
    "x_position": 50,
    "y_position": 50,
    "start_time": 0.0,
    "end_time": 10.0,
    "font_size": 32,
    "font_color": "white",
    "font_family": "Arial"
  }'
```

#### **Add Image Overlay**
```bash
POST /overlays/image
curl -X POST "http://localhost:8000/overlays/image" \
  -F "video_id=1" \
  -F "x_position=100" \
  -F "y_position=100" \
  -F "start_time=5.0" \
  -F "end_time=15.0" \
  -F "overlay_file=@overlay.png"
```

#### **Add Video Overlay**
```bash
POST /overlays/video
curl -X POST "http://localhost:8000/overlays/video" \
  -F "video_id=1" \
  -F "x_position=200" \
  -F "y_position=200" \
  -F "start_time=10.0" \
  -F "overlay_file=@overlay_video.mp4"
```

#### **Add Watermark**
```bash
POST /watermark
curl -X POST "http://localhost:8000/watermark" \
  -F "video_id=1" \
  -F "x_position=10" \
  -F "y_position=10" \
  -F "opacity=0.7" \
  -F "scale=0.5" \
  -F "watermark_file=@logo.png"
```

### **Async Operations (Level 4)**

#### **Async Video Upload**
```bash
POST /async/upload
curl -X POST "http://localhost:8000/async/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@video.mp4"

# Response:
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "video_id": 1,
  "message": "Video uploaded successfully, processing started"
}
```

#### **Async Trim**
```bash
POST /async/trim
curl -X POST "http://localhost:8000/async/trim" \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": 1,
    "start_time": 10.0,
    "end_time": 30.0
  }'
```

#### **Async Text Overlay**
```bash
POST /async/overlays/text
curl -X POST "http://localhost:8000/async/overlays/text" \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": 1,
    "content": "Async Text!",
    "x_position": 50,
    "y_position": 50
  }'
```

#### **Check Job Status**
```bash
GET /status/{job_id}
curl "http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000"

# Response:
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress_percentage": 50,
  "message": "Job is currently being processed"
}
```

#### **Get Job Result**
```bash
GET /result/{job_id}
curl "http://localhost:8000/result/550e8400-e29b-41d4-a716-446655440000" -o "result.mp4"
```

#### **Get All Jobs for Video**
```bash
GET /jobs/{video_id}
curl "http://localhost:8000/jobs/1"
```

### **Multiple Quality Outputs (Level 5)**

#### **Convert to Multiple Qualities**
```bash
POST /qualities/convert
curl -X POST "http://localhost:8000/qualities/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": 1,
    "qualities": ["1080p", "720p", "480p"]
  }'

# Response:
{
  "job_id": "quality-job-id-here",
  "message": "Quality conversion started for 3 variants",
  "qualities": ["1080p", "720p", "480p"]
}
```

#### **List Video Qualities**
```bash
GET /videos/{video_id}/qualities
curl "http://localhost:8000/videos/1/qualities"
```

#### **Download Specific Quality**
```bash
GET /videos/{video_id}/qualities/{quality}
curl "http://localhost:8000/videos/1/qualities/720p" -o "video_720p.mp4"
```

#### **Get Quality Information**
```bash
GET /videos/{video_id}/qualities/{quality}/info
curl "http://localhost:8000/videos/1/qualities/720p/info"

# Response:
{
  "id": 1,
  "original_video_id": 1,
  "quality": "720p",
  "filename": "720p_video.mp4",
  "file_size": 15728640,
  "width": 1280,
  "height": 720,
  "bitrate": "3000k",
  "is_processing": false,
  "created_at": "2025-09-20T10:30:00Z"
}
```

### **Utility Endpoints**

#### **Get Video Overlays**
```bash
GET /videos/{video_id}/overlays
curl "http://localhost:8000/videos/1/overlays"
```

#### **Get Video Watermarks**
```bash
GET /videos/{video_id}/watermarks
curl "http://localhost:8000/videos/1/watermarks"
```

#### **Get Trimmed Versions**
```bash
GET /videos/{video_id}/trimmed
curl "http://localhost:8000/videos/1/trimmed"
```

## 🌍 Indian Language Support

The text overlay feature supports Indian languages through system fonts:

### **Install Indian Language Fonts:**
```bash
# Ubuntu/Debian
sudo apt install fonts-noto-devanagari fonts-noto-bengali fonts-noto-tamil

# macOS (fonts usually pre-installed)
# Windows (download from Google Fonts)
```

### **Use Indian Languages in Text Overlays:**
```bash
curl -X POST "http://localhost:8000/overlays/text" \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": 1,
    "content": "नमस्ते दुनिया! স্বাগতম! வணக்கம்!",
    "font_family": "Noto Sans Devanagari",
    "font_size": 32,
    "font_color": "white"
  }'
```

## 📊 Database Schema

### **Videos Table**
```sql
videos (
  id SERIAL PRIMARY KEY,
  filename VARCHAR NOT NULL,
  original_filename VARCHAR NOT NULL,
  duration FLOAT,
  file_size INTEGER,
  width INTEGER,
  height INTEGER,
  fps FLOAT,
  upload_time TIMESTAMP DEFAULT NOW(),
  file_path VARCHAR NOT NULL,
  is_processed BOOLEAN DEFAULT FALSE
)
```

### **Trimmed Videos Table**
```sql
trimmed_videos (
  id SERIAL PRIMARY KEY,
  original_video_id INTEGER REFERENCES videos(id),
  filename VARCHAR NOT NULL,
  start_time FLOAT NOT NULL,
  end_time FLOAT NOT NULL,
  duration FLOAT NOT NULL,
  file_size INTEGER,
  file_path VARCHAR NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
)
```

### **Video Overlays Table**
```sql
video_overlays (
  id SERIAL PRIMARY KEY,
  video_id INTEGER REFERENCES videos(id),
  overlay_type VARCHAR NOT NULL, -- 'text', 'image', 'video'
  content TEXT, -- for text overlays
  file_path VARCHAR, -- for image/video overlays
  x_position INTEGER DEFAULT 0,
  y_position INTEGER DEFAULT 0,
  start_time FLOAT DEFAULT 0.0,
  end_time FLOAT,
  font_size INTEGER,
  font_color VARCHAR,
  font_family VARCHAR,
  created_at TIMESTAMP DEFAULT NOW()
)
```

### **Video Watermarks Table**
```sql
video_watermarks (
  id SERIAL PRIMARY KEY,
  video_id INTEGER REFERENCES videos(id),
  watermark_path VARCHAR NOT NULL,
  x_position INTEGER DEFAULT 10,
  y_position INTEGER DEFAULT 10,
  opacity FLOAT DEFAULT 1.0,
  scale FLOAT DEFAULT 1.0,
  created_at TIMESTAMP DEFAULT NOW()
)
```

### **Processing Jobs Table (Level 4)**
```sql
processing_jobs (
  id VARCHAR PRIMARY KEY, -- UUID
  job_type job_type_enum NOT NULL,
  status job_status_enum DEFAULT 'pending',
  video_id INTEGER REFERENCES videos(id),
  input_data TEXT, -- JSON
  result_data TEXT, -- JSON
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  started_at TIMESTAMP,
  completed_at TIMESTAMP
)
```

### **Video Variants Table (Level 5)**
```sql
video_variants (
  id SERIAL PRIMARY KEY,
  original_video_id INTEGER REFERENCES videos(id),
  quality video_quality_enum NOT NULL,
  filename VARCHAR NOT NULL,
  file_path VARCHAR NOT NULL,
  file_size INTEGER,
  width INTEGER NOT NULL,
  height INTEGER NOT NULL,
  bitrate VARCHAR,
  is_processing BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
)
```

## 🔄 Job Status Flow

### **Status Types:**
1. **`pending`** - Job created, waiting for worker
2. **`processing`** - Worker actively processing job
3. **`completed`** - Job finished successfully
4. **`failed`** - Job encountered an error

### **Job Types:**
- `upload_process` - Video upload processing
- `trim` - Video trimming
- `text_overlay` - Text overlay addition
- `image_overlay` - Image overlay addition  
- `video_overlay` - Video overlay addition
- `watermark` - Watermark addition
- `quality_conversion` - Multi-quality conversion

## 🎚️ Video Quality Settings

| Quality | Resolution | Bitrate | Use Case |
|---------|------------|---------|----------|
| **1080p** | 1920x1080 | 5000k | High-end devices, WiFi |
| **720p** | 1280x720 | 3000k | Standard HD, good connection |
| **480p** | 854x480 | 1500k | Mobile devices, 4G |
| **360p** | 640x360 | 800k | Low bandwidth, 3G |

## 🛠️ Troubleshooting

### **Common Issues and Solutions:**

#### **1. Database Connection Error**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -U postgres -d videoprocessing -c "SELECT 1;"

# Fix: Check DATABASE_URL in .env file
```

#### **2. Redis Connection Error**
```bash
# Check Redis status
redis-cli ping  # Should return PONG

# Restart Redis
sudo systemctl restart redis-server

# Fix: Check REDIS_URL in .env file
```

#### **3. FFmpeg Not Found**
```bash
# Test FFmpeg
ffmpeg -version

# Install if missing
sudo apt install ffmpeg  # Ubuntu
brew install ffmpeg      # macOS
```

#### **4. Celery Worker Not Starting**
```bash
# Check worker status
celery -A celery_config inspect active

# Kill existing workers
pkill -f celery

# Restart worker
python start_celery.py
```

#### **5. File Permission Errors**
```bash
# Fix directory permissions
sudo chown -R $USER:$USER uploads processed overlays watermarks
chmod 755 uploads processed overlays watermarks
```

#### **6. Migration Errors**
```bash
# Check current version
alembic current

# Reset migrations (if needed)
alembic downgrade base
alembic upgrade head

# Generate new migration
alembic revision --autogenerate -m "description"
```

#### **7. Job Processing Stuck**
```bash
# Clear Redis queue (careful!)
redis-cli FLUSHDB

# Restart services
sudo systemctl restart redis-server
python start_celery.py
```

## 📈 Performance Optimization

### **Production Recommendations:**

#### **Database Optimization:**
```sql
-- Add indexes for better performance
CREATE INDEX idx_videos_upload_time ON videos(upload_time);
CREATE INDEX idx_processing_jobs_status ON processing_jobs(status);
CREATE INDEX idx_video_variants_original_id ON video_variants(original_video_id);
```

#### **Celery Scaling:**
```bash
# Multiple workers
celery -A celery_config worker --concurrency=4

# Different queues
celery -A celery_config worker --queues=high_priority,normal_priority
```

#### **File Storage:**
- Use SSD storage for video processing
- Implement file cleanup for old processed videos
- Consider cloud storage (AWS S3, Google Cloud) for production

#### **Caching:**
- Add Redis caching for frequently accessed metadata
- Implement CDN for video delivery
- Cache processing results

## 🔐 Security Considerations

### **File Upload Security:**
- Validate file types and sizes
- Scan uploaded files for malware
- Limit upload rate per user
- Store files outside web root

### **API Security:**
- Implement authentication (JWT tokens)
- Add rate limiting
- Validate all input parameters
- Use HTTPS in production

### **Database Security:**
- Use parameterized queries (SQLAlchemy handles this)
- Limit database user permissions
- Enable PostgreSQL logging
- Regular security updates

## 🚀 Production Deployment

### **Docker Setup:**
```dockerfile
# Dockerfile example
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### **Environment Variables:**
```bash
# Production .env
DATABASE_URL=postgresql://user:pass@db:5432/videoprocessing
REDIS_URL=redis://redis:6379/0
ENVIRONMENT=production
```

### **Process Management:**
```bash
# Using supervisord or systemd
# Or PM2 for Node.js-style process management
```

### **Load Balancer:**
- Use Nginx for reverse proxy
- Load balance multiple FastAPI instances
- Serve static files directly from Nginx

## 📊 Monitoring & Logging

### **Application Monitoring:**
- Use Flower dashboard: http://localhost:5555
- Monitor job queue sizes
- Track processing times
- Set up alerts for failed jobs

### **System Monitoring:**
- Monitor disk space (videos consume storage)
- CPU usage during video processing
- Memory usage for large video files
- Redis memory usage

### **Logging Setup:**
```python
# Add to main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🧪 Testing Examples

### **Complete Workflow Test:**
```bash
# 1. Upload video
UPLOAD_RESPONSE=$(curl -s -X POST "http://localhost:8000/async/upload" \
  -F "file=@test_video.mp4")
JOB_ID=$(echo $UPLOAD_RESPONSE | jq -r '.job_id')
VIDEO_ID=$(echo $UPLOAD_RESPONSE | jq -r '.video_id')

# 2. Wait for processing
sleep 10

# 3. Check status
curl "http://localhost:8000/status/$JOB_ID"

# 4. Convert to multiple qualities
QUALITY_RESPONSE=$(curl -s -X POST "http://localhost:8000/qualities/convert" \
  -H "Content-Type: application/json" \
  -d "{\"video_id\": $VIDEO_ID, \"qualities\": [\"720p\", \"480p\"]}")
QUALITY_JOB_ID=$(echo $QUALITY_RESPONSE | jq -r '.job_id')

# 5. Wait for quality conversion
sleep 30

# 6. Download 720p version
curl "http://localhost:8000/videos/$VIDEO_ID/qualities/720p" -o "output_720p.mp4"

# 7. Add text overlay
curl -X POST "http://localhost:8000/async/overlays/text" \
  -H "Content-Type: application/json" \
  -d "{
    \"video_id\": $VIDEO_ID,
    \"content\": \"Test Overlay\",
    \"x_position\": 50,
    \"y_position\": 50
  }"
```

## 📞 Support & Contributing

### **Getting Help:**
1. Check this README for solutions
2. Review API documentation at `/docs`
3. Check logs for error details
4. Test with minimal examples

### **Contributing:**
1. Fork the repository
2. Create feature branch
3. Add tests for new features  
4. Submit pull request with description

### **Reporting Issues:**
- Include error messages
- Provide steps to reproduce
- Share environment details
- Attach sample files if relevant

---

## 🎉 **You're Ready to Process Videos!**

Your comprehensive video processing platform is now set up with:
- ✅ **5 Complete Levels** of functionality
- ✅ **Sync & Async** processing options  
- ✅ **Multiple quality** outputs
- ✅ **Indian language** support
- ✅ **Production-ready** architecture

**Start all services and visit http://localhost:8000/docs to explore your API! 🚀**