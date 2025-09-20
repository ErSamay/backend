#!/usr/bin/env python3
"""
Setup script for Video Processing API
This script helps set up the database and run migrations
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during {description}:")
        print(f"   Command: {command}")
        print(f"   Error: {e.stderr}")
        return False

def check_requirements():
    """Check if required software is installed"""
    print("🔍 Checking requirements...")
    
    # Check Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print("✅ Python version is compatible")
    
    # Check PostgreSQL
    try:
        subprocess.run("psql --version", shell=True, check=True, capture_output=True)
        print("✅ PostgreSQL is installed")
    except subprocess.CalledProcessError:
        print("❌ PostgreSQL is not installed or not in PATH")
        return False
    
    # Check FFmpeg
    try:
        subprocess.run("ffmpeg -version", shell=True, check=True, capture_output=True)
        print("✅ FFmpeg is installed")
    except subprocess.CalledProcessError:
        print("❌ FFmpeg is not installed or not in PATH")
        print("   Please install FFmpeg: sudo apt-get install ffmpeg (Ubuntu/Debian)")
        return False
    
    return True

def setup_environment():
    """Set up environment file"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📄 Creating .env file from template...")
        with open(env_example, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ .env file created")
        print("⚠️  Please edit .env file with your database credentials")
        return False
    elif env_file.exists():
        print("✅ .env file already exists")
        return True
    else:
        print("❌ No .env.example file found")
        return False

def install_dependencies():
    """Install Python dependencies"""
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python dependencies"
    )

def setup_database():
    """Initialize Alembic and run migrations"""
    print("🗄️ Setting up database...")
    
    # Initialize Alembic (if not already done)
    alembic_dir = Path("alembic")
    if not alembic_dir.exists():
        if not run_command("alembic init alembic", "Initializing Alembic"):
            return False
    
    # Run migrations
    if not run_command("alembic upgrade head", "Running database migrations"):
        return False
    
    return True

def create_directories():
    """Create required directories"""
    directories = ["uploads", "processed", "overlays", "watermarks"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def main():
    """Main setup function"""
    print("🚀 Setting up Video Processing API...\n")
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Setup failed: Missing requirements")
        sys.exit(1)
    
    # Setup environment
    env_ready = setup_environment()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Setup failed: Could not install dependencies")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Setup database (only if env is ready)
    if env_ready:
        if not setup_database():
            print("\n❌ Setup failed: Database setup failed")
            print("   Please check your database connection in .env file")
            sys.exit(1)
    else:
        print("\n⚠️  Database setup skipped - please configure .env file first")
        print("   After configuring .env, run: alembic upgrade head")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📚 Next steps:")
    if not env_ready:
        print("1. Edit .env file with your database credentials")
        print("2. Run: alembic upgrade head")
        print("3. Start the server: python main.py")
    else:
        print("1. Start the server: python main.py")
    print("2. Visit http://localhost:8000/docs for API documentation")

if __name__ == "__main__":
    main()