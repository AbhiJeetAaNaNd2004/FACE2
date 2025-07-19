# Face Recognition Attendance System

A fully functional backend for a face recognition-based attendance system built with FastAPI and PostgreSQL. This system provides role-based access control, JWT authentication, and comprehensive attendance tracking capabilities.

## Features

- **JWT-based Authentication** with OAuth2PasswordBearer
- **Role-Based Access Control (RBAC)** with three roles:
  - **Employee**: View own attendance, view currently present employees
  - **Admin**: All Employee permissions + enroll employees, manage face embeddings, delete records, view live feed
  - **Super Admin**: All Admin permissions + create/delete user accounts, assign roles
- **Face Recognition Integration** (mock implementation included, ready for real face recognition libraries)
- **Attendance Tracking** with comprehensive logging
- **Live Camera Feed** (mock MJPEG stream)
- **RESTful API** with comprehensive documentation

## Technology Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT with passlib[bcrypt]
- **Environment**: Compatible with Windows (development) and Linux (production)
- **No Docker Required**: Runs as a standalone application

## Database Schema

### Core Models

1. **Employee**
   - `employee_id` (Primary Key)
   - `name`, `department`, `role`, `date_joined`
   - `email`, `phone`, `is_active`

2. **FaceEmbedding**
   - `id` (Primary Key)
   - `employee_id` (Foreign Key)
   - `image_path`, `embedding_vector`
   - `quality_score`, `is_active`

3. **AttendanceLog**
   - `id` (Primary Key)
   - `employee_id` (Foreign Key)
   - `timestamp`, `status` (present/absent)
   - `confidence_score`, `notes`

4. **UserAccount**
   - `id` (Primary Key)
   - `username`, `hashed_password`, `role`
   - `employee_id` (Optional Foreign Key)
   - `is_active`, `last_login`

## Installation & Setup

### Prerequisites

1. **Python 3.8+**
2. **PostgreSQL 12+**
3. **Git**

### 1. Clone the Repository

```bash
git clone <repository-url>
cd face-recognition-attendance
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

#### PostgreSQL Installation

**Windows:**
```bash
# Download and install PostgreSQL from https://www.postgresql.org/download/windows/
# Or use chocolatey:
choco install postgresql

# Create database
psql -U postgres
CREATE DATABASE face_attendance;
\q
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql postgresql-server postgresql-contrib

# Create database
sudo -u postgres psql
CREATE DATABASE face_attendance;
\q
```

### 4. Environment Configuration

Create a `.env` file in the `backend` directory:

```bash
cp backend/.env.example backend/.env
```

Update the `.env` file with your database credentials:

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

### 5. Initialize Database

```bash
cd backend
python init_db.py
```

This will create all necessary tables and sample data including test users.

### 6. Start the Application

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Authentication

- `POST /auth/login` - Login with OAuth2PasswordRequestForm
- `POST /auth/login/json` - Login with JSON data
- `GET /auth/me` - Get current user info
- `POST /auth/users/create` - Create user account (Super Admin only)
- `PATCH /auth/users/{user_id}/role` - Assign role (Super Admin only)
- `GET /auth/users` - List all users (Super Admin only)
- `DELETE /auth/users/{user_id}` - Delete user (Super Admin only)

### Employee Management

- `POST /employees/enroll` - Enroll employee with face data (Admin+)
- `GET /employees/` - List all employees (Any authenticated user)
- `GET /employees/{employee_id}` - Get employee details
- `PUT /employees/{employee_id}` - Update employee (Admin+)
- `DELETE /employees/{employee_id}` - Delete employee (Admin+)
- `GET /employees/present/current` - Get currently present employees
- `POST /employees/{employee_id}/face-image` - Upload face image (Admin+)

### Attendance Management

- `GET /attendance/me` - Get own attendance (Employee+)
- `GET /attendance/all` - Get all attendance records (Admin+)
- `GET /attendance/{employee_id}` - Get employee attendance
- `POST /attendance/mark` - Mark attendance (Admin+)
- `GET /attendance/summary/daily` - Daily attendance summary (Admin+)
- `DELETE /attendance/{log_id}` - Delete attendance log (Admin+)
- `GET /attendance/employee/{employee_id}/latest` - Get latest attendance

### Face Embeddings

- `GET /embeddings/` - List face embeddings (Admin+)
- `GET /embeddings/{embedding_id}` - Get specific embedding (Admin+)
- `DELETE /embeddings/{embedding_id}` - Delete embedding (Admin+)
- `GET /embeddings/employee/{employee_id}` - Get employee embeddings (Admin+)
- `DELETE /embeddings/employee/{employee_id}/all` - Delete all employee embeddings (Admin+)
- `GET /embeddings/stats/summary` - Get embeddings statistics (Admin+)

### Live Streaming

- `GET /stream/live-feed` - Get live camera feed (Admin+)
- `GET /stream/camera-status` - Get camera status (Admin+)
- `GET /stream/health` - Streaming health check (Admin+)

## Sample Login Credentials

The initialization script creates the following test users:

| Username | Password | Role | Employee ID |
|----------|----------|------|-------------|
| admin | admin123 | super_admin | None |
| hr_manager | hr123 | admin | EMP002 |
| john.doe | john123 | employee | EMP001 |
| bob.johnson | bob123 | employee | EMP003 |

## Role-Based Access Control

### Employee Role
- View own attendance records
- View list of currently present employees
- View employee directory

### Admin Role
- All Employee permissions
- Enroll new employees with face data
- Add/delete face embeddings
- Mark attendance for employees
- Delete attendance records
- View live camera feed
- Access attendance summaries

### Super Admin Role
- All Admin permissions
- Create/delete user accounts
- Assign roles to users
- Full system administration

## Usage Examples

### 1. Authentication

```bash
# Login to get JWT token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. Employee Enrollment

```bash
# Enroll employee with face data (Admin+ only)
curl -X POST "http://localhost:8000/employees/enroll" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee": {
      "employee_id": "EMP004",
      "name": "Alice Johnson",
      "department": "Marketing",
      "role": "Marketing Manager",
      "date_joined": "2024-01-01",
      "email": "alice@company.com"
    },
    "image_data": "base64_encoded_image_data_here"
  }'
```

### 3. View Own Attendance

```bash
# Get own attendance records
curl -X GET "http://localhost:8000/attendance/me" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Mark Attendance

```bash
# Mark attendance (Admin+ only)
curl -X POST "http://localhost:8000/attendance/mark" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "employee_id": "EMP001",
    "status": "present",
    "confidence_score": 0.95,
    "notes": "Automatic detection"
  }'
```

## Deployment

### Production Deployment

1. **Set Environment Variables**:
   ```bash
   export ENVIRONMENT=production
   export DEBUG=false
   export SECRET_KEY=your-production-secret-key
   ```

2. **Use Production Database**:
   Update database credentials in `.env` file

3. **Run with Gunicorn**:
   ```bash
   pip install gunicorn
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

4. **Nginx Configuration** (optional):
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Windows Service (Production)

Create a Windows service using `nssm` or similar tools:

```bash
# Install nssm
nssm install FaceAttendanceAPI

# Configure service
nssm set FaceAttendanceAPI Application "C:\path\to\python.exe"
nssm set FaceAttendanceAPI AppParameters "-m uvicorn app.main:app --host 0.0.0.0 --port 8000"
nssm set FaceAttendanceAPI AppDirectory "C:\path\to\your\backend"
nssm start FaceAttendanceAPI
```

## Development

### Adding Face Recognition

To integrate real face recognition capabilities:

1. **Install face recognition libraries**:
   ```bash
   pip install opencv-python face-recognition numpy Pillow
   ```

2. **Update the enrollment process** in `backend/app/routers/employees.py`
3. **Implement face matching** in attendance marking logic
4. **Add real-time face detection** in the streaming module

### Database Migrations

For database schema changes, use Alembic:

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Description of changes"

# Apply migration
alembic upgrade head
```

## Troubleshooting

### Common Issues

1. **Database Connection Error**:
   - Check PostgreSQL is running
   - Verify database credentials in `.env`
   - Ensure database exists

2. **JWT Token Issues**:
   - Check `SECRET_KEY` in `.env`
   - Verify token expiration time
   - Ensure proper Authorization header format

3. **Permission Denied**:
   - Check user role assignments
   - Verify JWT token is valid
   - Ensure user is active

4. **Import Errors**:
   - Check Python path
   - Verify all dependencies are installed
   - Ensure you're in the correct directory

### Logs

Application logs are available in:
- Console output (development)
- Log files (production, if configured)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the API documentation at `/docs`
- Review the troubleshooting section
- Create an issue in the repository