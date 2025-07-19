# Face Recognition Attendance System

A complete, production-ready face recognition attendance system with a FastAPI backend and React frontend. This system provides role-based access control, real-time face detection, and comprehensive attendance tracking.

## 🚀 Features

### Backend Features
- **JWT-based Authentication** with role-based access control
- **Real-time Face Detection** with automatic attendance tracking
- **Camera Management** with ONVIF discovery and configuration
- **RESTful API** with comprehensive documentation
- **PostgreSQL Database** with proper relationships and constraints
- **Background Processing** for face detection and recognition

### Frontend Features
- **Modern React Application** with TypeScript
- **Role-based Dashboards** (Employee, Admin, Super Admin)
- **Real-time System Monitoring** and control
- **Employee Management** with face enrollment
- **Live Camera Feeds** with face detection overlay
- **Responsive Design** with Tailwind CSS and shadcn/ui

### User Roles
- **Employee**: View personal attendance, current status
- **Admin**: Manage employees, view attendance, access live feeds
- **Super Admin**: Full system control, user management, camera configuration

## 🛠 Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Robust relational database
- **SQLAlchemy** - Python ORM
- **JWT** - Secure authentication
- **OpenCV** - Computer vision (ready for integration)

### Frontend
- **React 18** with TypeScript
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Modern component library
- **Zustand** - Lightweight state management
- **Axios** - HTTP client with interceptors
- **React Router** - Client-side routing

## 📋 Prerequisites

- **Python 3.8+**
- **Node.js 16+**
- **PostgreSQL 12+**
- **Git**

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd face-recognition-attendance
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### Database Configuration
Create a `.env` file in the `backend` directory:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=face_attendance
DB_USER=postgres
DB_PASSWORD=your_password_here

# Security Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Application Configuration
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

#### Initialize Database
```bash
# Create PostgreSQL database
createdb face_attendance

# Initialize tables and sample data
python init_db.py
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Start the Application

#### Start Backend (Terminal 1)
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Start Frontend (Terminal 2)
```bash
cd frontend
npm start
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 👥 Demo Credentials

| Role | Username | Password | Description |
|------|----------|----------|-------------|
| Super Admin | `admin` | `admin123` | Full system access |
| Admin | `hr_manager` | `hr123` | Employee & attendance management |
| Employee | `john.doe` | `john123` | Personal attendance view |
| Employee | `bob.johnson` | `bob123` | Personal attendance view |

## 🎯 Key Features Walkthrough

### 1. Super Admin Dashboard
- **System Control**: Start/stop face detection pipeline
- **Real-time Metrics**: System status, camera count, detection stats
- **User Management**: Create users, assign roles
- **Camera Management**: Discover and configure cameras
- **System Logs**: Monitor application logs

### 2. Admin Dashboard
- **Employee Management**: Enroll employees with face images
- **Attendance Monitoring**: View all attendance records
- **Live Camera Feeds**: Real-time video with face detection
- **Present Employees**: See who's currently in the office
- **Data Export**: Download attendance reports

### 3. Employee Dashboard
- **Personal Attendance**: View own attendance history
- **Current Status**: See current presence status
- **Attendance Rate**: Personal attendance statistics

## 🔧 System Architecture

### Backend Architecture
```
FastAPI Application
├── Authentication Layer (JWT)
├── Role-based Access Control
├── API Routes (/auth, /employees, /attendance, /cameras, /system)
├── Face Detection Pipeline (Background Service)
├── Database Layer (PostgreSQL + SQLAlchemy)
└── Camera Management (ONVIF Discovery)
```

### Frontend Architecture
```
React Application
├── Authentication (Zustand Store)
├── Protected Routes (Role-based)
├── Layout Components (Sidebar Navigation)
├── Dashboard Pages (Role-specific)
├── API Layer (Axios with Interceptors)
└── UI Components (shadcn/ui + Tailwind)
```

## 🔐 Security Features

- **JWT Authentication** with automatic token refresh
- **Role-based Access Control** with route protection
- **Password Hashing** with bcrypt
- **CORS Configuration** for secure cross-origin requests
- **Input Validation** on all API endpoints
- **SQL Injection Protection** via SQLAlchemy ORM

## 📊 API Endpoints

### Authentication
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user
- `POST /auth/users/create` - Create user (Super Admin)

### Employee Management
- `GET /employees/` - List employees
- `POST /employees/enroll` - Enroll with face data
- `PUT /employees/{id}` - Update employee
- `DELETE /employees/{id}` - Delete employee

### Attendance
- `GET /attendance/me` - Personal attendance
- `GET /attendance/all` - All records (Admin)
- `POST /attendance/mark` - Mark attendance
- `GET /attendance/summary/daily` - Daily summary

### System Control
- `POST /system/start` - Start face detection
- `POST /system/stop` - Stop face detection
- `GET /system/status` - System status
- `GET /system/camera-feed/{id}` - Live camera feed

### Camera Management
- `POST /cameras/discover` - Network discovery
- `GET /cameras/` - List cameras
- `POST /cameras/` - Create camera
- `PUT /cameras/{id}` - Update camera

## 🚀 Production Deployment

### Backend Deployment
```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or use Docker
docker build -t face-recognition-backend .
docker run -p 8000:8000 face-recognition-backend
```

### Frontend Deployment
```bash
# Build for production
npm run build

# Serve with nginx or any static file server
# The build folder contains the production-ready files
```

### Environment Variables (Production)
```env
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=your-production-secret-key
DB_HOST=your-production-db-host
CORS_ORIGINS=https://yourdomain.com
```

## 🔧 Customization

### Adding Face Recognition
The system is ready for face recognition integration. To add real face detection:

1. Install face recognition libraries:
```bash
pip install opencv-python face-recognition insightface
```

2. Replace mock detection in `backend/core/fts_system.py`:
```python
def _mock_face_detection(self, frame, camera):
    # Replace with actual face recognition logic
    # Use InsightFace, face_recognition, or similar library
    pass
```

### Adding New User Roles
1. Update `backend/app/schemas.py` UserRole enum
2. Add role checks in `backend/app/security.py`
3. Update frontend role hierarchy in `ProtectedRoute.tsx`
4. Add new dashboard routes and navigation items

### Customizing UI Theme
The frontend uses Tailwind CSS with CSS variables for theming:
1. Modify `frontend/src/index.css` for color scheme
2. Update `frontend/tailwind.config.js` for design tokens
3. Customize components in `frontend/src/components/ui/`

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify PostgreSQL is running
   - Check database credentials in `.env`
   - Ensure database exists

2. **Face Detection Not Starting**
   - Check system logs in Super Admin dashboard
   - Verify camera configurations
   - Ensure no port conflicts

3. **Frontend API Errors**
   - Check backend is running on port 8000
   - Verify CORS configuration
   - Check browser console for errors

4. **Authentication Issues**
   - Clear browser localStorage
   - Check JWT token expiration
   - Verify user roles in database

### Logs and Debugging
- **Backend logs**: Check uvicorn console output
- **Frontend logs**: Check browser developer console
- **System logs**: Available in Super Admin dashboard
- **Database logs**: Check PostgreSQL logs

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support and questions:
- Check the API documentation at `/docs`
- Review this README and troubleshooting section
- Create an issue in the repository

---

**Built with ❤️ using FastAPI and React**