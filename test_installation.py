#!/usr/bin/env python3
"""
Test script to verify Face Recognition Attendance System installation
"""

import sys
import os
import requests
import time
import subprocess
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Add backend to path
        backend_path = Path(__file__).parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        # Test core imports
        from app.main import app
        from app.config import settings
        from app.schemas import UserRole, AttendanceStatus
        from app.security import get_password_hash, verify_password
        from db.db_models import Employee, UserAccount, AttendanceLog, FaceEmbedding
        from db.db_config import create_tables
        
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_password_hashing():
    """Test password hashing functionality"""
    print("🔍 Testing password hashing...")
    
    try:
        from app.security import get_password_hash, verify_password
        
        password = "test123"
        hashed = get_password_hash(password)
        
        if verify_password(password, hashed):
            print("✅ Password hashing works correctly")
            return True
        else:
            print("❌ Password verification failed")
            return False
    except Exception as e:
        print(f"❌ Password hashing error: {e}")
        return False

def test_database_models():
    """Test database models creation"""
    print("🔍 Testing database models...")
    
    try:
        from db.db_models import Employee, UserAccount, AttendanceLog, FaceEmbedding
        from datetime import date, datetime
        
        # Test model creation (without saving to DB)
        employee = Employee(
            employee_id="TEST001",
            name="Test Employee",
            department="Testing",
            role="Tester",
            date_joined=date.today()
        )
        
        user = UserAccount(
            username="testuser",
            hashed_password="hashed_password_here",
            role="employee"
        )
        
        attendance = AttendanceLog(
            employee_id="TEST001",
            status="present",
            timestamp=datetime.now()
        )
        
        embedding = FaceEmbedding(
            employee_id="TEST001",
            image_path="/path/to/image.jpg",
            embedding_vector=b"test_embedding_data"
        )
        
        print("✅ Database models created successfully")
        return True
    except Exception as e:
        print(f"❌ Database models error: {e}")
        return False

def test_api_server():
    """Test if the API server can start and respond"""
    print("🔍 Testing API server startup...")
    
    try:
        backend_path = Path(__file__).parent / "backend"
        
        # Start server in background
        server_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", "127.0.0.1",
            "--port", "8001"
        ], cwd=str(backend_path), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        # Test health endpoint
        try:
            response = requests.get("http://127.0.0.1:8001/health", timeout=5)
            if response.status_code == 200:
                print("✅ API server started and responding")
                result = True
            else:
                print(f"❌ API server returned status code: {response.status_code}")
                result = False
        except requests.exceptions.RequestException as e:
            print(f"❌ API server connection error: {e}")
            result = False
        
        # Stop server
        server_process.terminate()
        server_process.wait()
        
        return result
        
    except Exception as e:
        print(f"❌ API server test error: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("🔍 Testing configuration...")
    
    try:
        from app.config import settings
        
        # Check required settings
        required_settings = [
            'DATABASE_URL', 'SECRET_KEY', 'ALGORITHM', 
            'ACCESS_TOKEN_EXPIRE_MINUTES', 'CORS_ORIGINS'
        ]
        
        for setting in required_settings:
            if not hasattr(settings, setting):
                print(f"❌ Missing configuration: {setting}")
                return False
        
        print("✅ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Face Recognition Attendance System - Installation Test")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Password Hashing", test_password_hashing),
        ("Database Models", test_database_models),
        ("Configuration", test_configuration),
        ("API Server", test_api_server),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Installation is working correctly.")
        print("\nNext steps:")
        print("1. Set up your PostgreSQL database")
        print("2. Update backend/.env with your database credentials")
        print("3. Run: python start_server.py --init-db")
        print("4. Run: python start_server.py --reload")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)