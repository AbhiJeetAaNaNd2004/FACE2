#!/usr/bin/env python3
"""
Face Detection System Startup Script
Starts the face detection system by making an API call to the FastAPI server
"""

import requests
import json
import time
import sys
from pathlib import Path

def get_auth_token():
    """Get authentication token for API calls"""
    # You'll need to modify this with actual credentials
    # For now, this is a placeholder
    login_data = {
        "username": "admin",  # Replace with actual admin username
        "password": "admin"   # Replace with actual admin password
    }
    
    try:
        response = requests.post("http://localhost:8000/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"❌ Failed to authenticate: {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error during authentication: {e}")
        return None

def start_face_detection():
    """Start the face detection system"""
    print("🔐 Authenticating...")
    token = get_auth_token()
    
    if not token:
        print("❌ Authentication failed. Please check your credentials.")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("🚀 Starting face detection system...")
        response = requests.post("http://localhost:8000/system/start", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Face detection system started successfully!")
                return True
            else:
                print(f"❌ Failed to start: {result.get('message')}")
                return False
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error starting face detection system: {e}")
        return False

def check_system_status():
    """Check the current status of the face detection system"""
    print("🔐 Authenticating...")
    token = get_auth_token()
    
    if not token:
        print("❌ Authentication failed. Please check your credentials.")
        return False
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        print("📊 Checking system status...")
        response = requests.get("http://localhost:8000/system/status", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                status_data = result.get("data", {})
                print(f"✅ System Status:")
                print(f"   - Running: {status_data.get('is_running', False)}")
                print(f"   - Uptime: {status_data.get('uptime', 0):.2f} seconds")
                print(f"   - Cameras: {status_data.get('cam_count', 0)}")
                print(f"   - Faces Detected: {status_data.get('faces_detected', 0)}")
                print(f"   - Attendance Count: {status_data.get('attendance_count', 0)}")
                return True
            else:
                print(f"❌ Failed to get status: {result.get('message')}")
                return False
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking system status: {e}")
        return False

def main():
    """Main function"""
    print("🎯 Face Detection System Manager")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            success = start_face_detection()
            if success:
                print("\n💡 You can now:")
                print("   - Check status: python start_face_detection.py status")
                print("   - View live feeds at: http://localhost:8000/system/camera-feed/{camera_id}")
                print("   - Monitor logs at: http://localhost:8000/system/logs")
            sys.exit(0 if success else 1)
            
        elif command == "status":
            success = check_system_status()
            sys.exit(0 if success else 1)
            
        else:
            print(f"❌ Unknown command: {command}")
            print("Usage: python start_face_detection.py [start|status]")
            sys.exit(1)
    else:
        print("Usage: python start_face_detection.py [start|status]")
        print("\nCommands:")
        print("  start  - Start the face detection system")
        print("  status - Check system status")
        sys.exit(1)

if __name__ == "__main__":
    main()