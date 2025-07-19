"""
Database initialization script
Creates sample users and data for testing the face recognition attendance system
"""

import os
import sys
from datetime import date, datetime

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from db.db_config import SessionLocal, create_tables
from db.db_models import UserAccount, Employee, AttendanceLog
from app.security import get_password_hash

def create_sample_data():
    """Create sample users and employees for testing"""
    db = SessionLocal()
    
    try:
        # Create sample employees
        employees = [
            {
                "employee_id": "EMP001",
                "name": "John Doe",
                "department": "Engineering",
                "role": "Software Engineer",
                "date_joined": date(2023, 1, 15),
                "email": "john.doe@company.com",
                "phone": "+1234567890"
            },
            {
                "employee_id": "EMP002",
                "name": "Jane Smith",
                "department": "HR",
                "role": "HR Manager",
                "date_joined": date(2023, 2, 1),
                "email": "jane.smith@company.com",
                "phone": "+1234567891"
            },
            {
                "employee_id": "EMP003",
                "name": "Bob Johnson",
                "department": "Engineering",
                "role": "Senior Developer",
                "date_joined": date(2023, 3, 10),
                "email": "bob.johnson@company.com",
                "phone": "+1234567892"
            }
        ]
        
        for emp_data in employees:
            existing_emp = db.query(Employee).filter(
                Employee.employee_id == emp_data["employee_id"]
            ).first()
            
            if not existing_emp:
                employee = Employee(**emp_data)
                db.add(employee)
                print(f"Created employee: {emp_data['name']} ({emp_data['employee_id']})")
        
        # Create sample user accounts
        users = [
            {
                "username": "admin",
                "password": "admin123",
                "role": "super_admin",
                "employee_id": None
            },
            {
                "username": "hr_manager",
                "password": "hr123",
                "role": "admin",
                "employee_id": "EMP002"
            },
            {
                "username": "john.doe",
                "password": "john123",
                "role": "employee",
                "employee_id": "EMP001"
            },
            {
                "username": "bob.johnson",
                "password": "bob123",
                "role": "employee",
                "employee_id": "EMP003"
            }
        ]
        
        for user_data in users:
            existing_user = db.query(UserAccount).filter(
                UserAccount.username == user_data["username"]
            ).first()
            
            if not existing_user:
                hashed_password = get_password_hash(user_data["password"])
                user = UserAccount(
                    username=user_data["username"],
                    hashed_password=hashed_password,
                    role=user_data["role"],
                    employee_id=user_data["employee_id"]
                )
                db.add(user)
                print(f"Created user: {user_data['username']} (role: {user_data['role']})")
        
        # Create sample attendance logs
        attendance_logs = [
            {
                "employee_id": "EMP001",
                "status": "present",
                "confidence_score": 0.95,
                "notes": "Automatic detection",
                "timestamp": datetime(2024, 1, 15, 9, 0, 0)
            },
            {
                "employee_id": "EMP002",
                "status": "present",
                "confidence_score": 0.92,
                "notes": "Automatic detection",
                "timestamp": datetime(2024, 1, 15, 9, 15, 0)
            },
            {
                "employee_id": "EMP001",
                "status": "absent",
                "confidence_score": None,
                "notes": "Manual entry",
                "timestamp": datetime(2024, 1, 16, 9, 0, 0)
            }
        ]
        
        for log_data in attendance_logs:
            attendance_log = AttendanceLog(**log_data)
            db.add(attendance_log)
        
        print("Created sample attendance logs")
        
        db.commit()
        print("\n✅ Sample data created successfully!")
        
        # Print login credentials
        print("\n🔑 Sample Login Credentials:")
        print("=" * 50)
        print("Super Admin:")
        print("  Username: admin")
        print("  Password: admin123")
        print("  Role: super_admin")
        print("\nAdmin (HR Manager):")
        print("  Username: hr_manager")
        print("  Password: hr123")
        print("  Role: admin")
        print("\nEmployee (John Doe):")
        print("  Username: john.doe")
        print("  Password: john123")
        print("  Role: employee")
        print("\nEmployee (Bob Johnson):")
        print("  Username: bob.johnson")
        print("  Password: bob123")
        print("  Role: employee")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """Main function to initialize database and create sample data"""
    print("🚀 Initializing Face Recognition Attendance System Database")
    print("=" * 60)
    
    try:
        # Create tables
        print("Creating database tables...")
        create_tables()
        print("✅ Database tables created successfully!")
        
        # Create sample data
        print("\nCreating sample data...")
        create_sample_data()
        
        print("\n🎯 Database initialization completed successfully!")
        print("\nYou can now start the API server with:")
        print("  uvicorn app.main:app --reload")
        print("\nAPI Documentation will be available at:")
        print("  http://localhost:8000/docs")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()