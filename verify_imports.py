#!/usr/bin/env python3
"""
Import verification script for Face Recognition Attendance System
This script verifies all imports are working correctly and provides guidance for fixing issues.
"""

import sys
import os
from pathlib import Path

def main():
    print("🔍 Face Recognition Attendance System - Import Verification")
    print("=" * 60)
    
    # Add backend to path
    backend_path = Path(__file__).parent / "backend"
    sys.path.insert(0, str(backend_path))
    
    print(f"✅ Added backend path: {backend_path}")
    print(f"✅ Python path: {sys.path[:3]}...")  # Show first 3 entries
    
    # Check if all required files exist
    print("\n📁 Checking file structure...")
    required_files = [
        "backend/__init__.py",
        "backend/app/__init__.py", 
        "backend/app/routers/__init__.py",
        "backend/core/__init__.py",
        "backend/db/__init__.py",
        "backend/db/db_models.py",
        "backend/db/db_manager.py",
        "backend/db/db_config.py"
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MISSING!")
            
    # Test imports step by step
    print("\n🧪 Testing imports...")
    
    try:
        print("  Testing db.db_models...")
        from db.db_models import Employee, FaceEmbedding, AttendanceLog, TrackingRecord, SystemLog, UserAccount, CameraConfig, Tripwire
        print("  ✅ db.db_models - All classes imported successfully")
        
        print("  Testing db.db_config...")
        from db.db_config import SessionLocal, get_db, create_tables
        print("  ✅ db.db_config - All functions imported successfully")
        
        print("  Testing db.db_manager...")
        from db.db_manager import DatabaseManager
        print("  ✅ db.db_manager - DatabaseManager imported successfully")
        
        print("  Testing app modules...")
        from app.main import app
        from app.config import settings
        print("  ✅ app modules - Main app and config imported successfully")
        
        print("  Testing routers...")
        from app.routers import auth, employees, attendance, embeddings, streaming, cameras
        print("  ✅ routers - All routers imported successfully")
        
        print("  Testing core modules...")
        from core.fts_system import FaceTrackingPipeline
        from core.face_enroller import FaceEnrollmentError
        print("  ✅ core modules - All core classes imported successfully")
        
        print("  Testing utils...")
        from utils.camera_discovery import discover_cameras_on_network
        from utils.logging import get_logger
        print("  ✅ utils - All utility functions imported successfully")
        
        print("\n🎉 ALL IMPORTS SUCCESSFUL!")
        print("\nIf you're still getting import errors, try:")
        print("1. Clear Python cache: python -Bc \"import shutil; shutil.rmtree('__pycache__', ignore_errors=True)\"")
        print("2. Restart your Python interpreter/IDE")
        print("3. Make sure you're running from the correct directory")
        print("4. Check that there are no conflicting db_models.py files in your environment")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nDebugging information:")
        print(f"  Error type: {type(e).__name__}")
        print(f"  Error message: {str(e)}")
        print(f"  Current working directory: {os.getcwd()}")
        print(f"  Backend path exists: {backend_path.exists()}")
        
        # Check specific file that's causing issues
        if "db_models" in str(e):
            db_models_path = backend_path / "db" / "db_models.py"
            print(f"  db_models.py exists: {db_models_path.exists()}")
            if db_models_path.exists():
                print(f"  db_models.py size: {db_models_path.stat().st_size} bytes")
        
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)