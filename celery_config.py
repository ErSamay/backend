from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "video_processor",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['celery_tasks']
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_routes={
        'celery_tasks.process_video_upload': {'queue': 'video_processing'},
        'celery_tasks.trim_video_async': {'queue': 'video_processing'},
        'celery_tasks.add_overlay_async': {'queue': 'video_processing'},
        'celery_tasks.add_watermark_async': {'queue': 'video_processing'},
        'celery_tasks.convert_video_qualities': {'queue': 'video_processing'},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

if __name__ == '__main__':
    celery_app.start()