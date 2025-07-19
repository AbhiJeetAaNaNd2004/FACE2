#!/usr/bin/env python3
"""
Startup script for Face Recognition Attendance System
Handles environment setup, database initialization, and server startup
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import psycopg2
        import passlib
        import jose
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install requirements with: pip install -r requirements.txt")
        return False

def check_database_connection():
    """Check if database connection is working"""
    try:
        # Add backend to path
        backend_path = Path(__file__).parent / "backend"
        sys.path.insert(0, str(backend_path))
        
        from app.config import settings
        from db.db_config import engine
        
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please check your database configuration in backend/.env")
        return False

def initialize_database():
    """Initialize database with tables and sample data"""
    try:
        backend_path = Path(__file__).parent / "backend"
        init_script = backend_path / "init_db.py"
        
        if init_script.exists():
            print("🔄 Initializing database...")
            result = subprocess.run([sys.executable, str(init_script)], 
                                  cwd=str(backend_path), 
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode == 0:
                print("✅ Database initialized successfully")
                return True
            else:
                print(f"❌ Database initialization failed: {result.stderr}")
                return False
        else:
            print("❌ Database initialization script not found")
            return False
    except Exception as e:
        print(f"❌ Error during database initialization: {e}")
        return False

def start_server(host="0.0.0.0", port=8000, reload=False, workers=1):
    """Start the FastAPI server"""
    try:
        backend_path = Path(__file__).parent / "backend"
        os.chdir(backend_path)
        
        # Build uvicorn command
        cmd = [
            sys.executable, "-m", "uvicorn",
            "app.main:app",
            "--host", host,
            "--port", str(port)
        ]
        
        if reload:
            cmd.append("--reload")
        
        if workers > 1 and not reload:
            cmd.extend(["--workers", str(workers)])
        
        print(f"🚀 Starting server on http://{host}:{port}")
        print(f"📚 API Documentation: http://{host}:{port}/docs")
        print("Press Ctrl+C to stop the server")
        
        # Start server
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Face Recognition Attendance System Startup Script"
    )
    
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="Host to bind the server to (default: 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind the server to (default: 8000)"
    )
    
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1, 
        help="Number of worker processes (default: 1)"
    )
    
    parser.add_argument(
        "--skip-checks", 
        action="store_true", 
        help="Skip pre-startup checks"
    )
    
    parser.add_argument(
        "--init-db", 
        action="store_true", 
        help="Initialize database and exit"
    )
    
    args = parser.parse_args()
    
    print("🎯 Face Recognition Attendance System")
    print("=" * 50)
    
    # Initialize database only
    if args.init_db:
        if not check_requirements():
            sys.exit(1)
        
        if not initialize_database():
            sys.exit(1)
        
        print("✅ Database initialization completed")
        return
    
    # Pre-startup checks
    if not args.skip_checks:
        print("🔍 Running pre-startup checks...")
        
        if not check_requirements():
            sys.exit(1)
        
        if not check_database_connection():
            print("\n💡 Tip: Try running with --init-db to initialize the database")
            sys.exit(1)
    
    # Start server
    start_server(
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers
    )

if __name__ == "__main__":
    main()