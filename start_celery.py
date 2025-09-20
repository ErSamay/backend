#!/usr/bin/env python3
"""
Start Celery worker for video processing tasks
"""

import subprocess
import sys
import os
from pathlib import Path

def start_celery_worker():
    """Start Celery worker"""
    print("🚀 Starting Celery worker for video processing...")
    
    try:
        # Start celery worker
        cmd = [
            "celery", "-A", "celery_config", "worker",
            "--loglevel=info",
            "--concurrency=2",
            "--queues=video_processing"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Celery worker stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Celery worker: {e}")
        sys.exit(1)

def start_flower_monitoring():
    """Start Flower monitoring (optional)"""
    print("🌸 Starting Flower monitoring dashboard...")
    
    try:
        cmd = [
            "celery", "-A", "celery_config", "flower",
            "--port=5555"
        ]
        
        print(f"Running: {' '.join(cmd)}")
        print("📊 Flower dashboard will be available at: http://localhost:5555")
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Flower monitoring stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting Flower: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "flower":
        start_flower_monitoring()
    else:
        start_celery_worker()