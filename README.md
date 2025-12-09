# Scope Attendance

A full-stack attendance tracking application for Scope CS Club built with Next.js, SQLite, TypeScript, and Python.

**Team Members:** Joyce Ng, Kasra Farsoudi

## Features

- 🔐 **Authentication**: Token-based login system
- 📊 **Dashboard**: View all users and mark attendance for today
- 👤 **User Management**: Add new users with profile information
- 📈 **Statistics**: View attendance by team, graduating class, and most active users
- 📝 **User Profiles**: Individual attendance records for each user
- 🎨 **Modern UI**: Polished interface with Scope branding
- 🤖 **Automated Face Recognition**: GPU-powered face detection and recognition
- 📹 **RPi Webcam Integration**: Real-time attendance check-in via camera

## Setup

### Web Application

1. **Install dependencies:**
```bash
npm install
```

2. **Initialize the database:**
```bash
npm run init-db
```

This creates:
- `users` table (id, name, email, password_hash, team, major, dob, graduating_class, profile_pic_path)
- `attendance` table (id, user_id, date, checked_off_at)
- `sessions` table (id, user_id, token, expires_at)
- Default admin user: `admin@scope.com` / `admin123`

3. **Start the development server:**
```bash
npm run dev
```

4. **Open your browser:**
Navigate to [http://localhost:3000](http://localhost:3000)

### GPU Server (Face Recognition)

Located in `gpu stuff/`

1. **Run the setup script:**
```bash
cd "gpu stuff"
./setup.sh
```

2. **Build face encodings:**
```bash
source venv/bin/activate
python build_encodings.py
```

This generates `encodings/face_encodings.npz` from the dataset.

3. **Start the face recognition service:**
```bash
source venv/bin/activate
python face_recognition_service.py
```

The service runs on `0.0.0.0:3005` and exposes:
- `GET /health` - Health check
- `POST /recognize` - Face recognition endpoint (accepts image via multipart form-data or base64 JSON)

### RPi Webcam Client

Located in `rpi stuff/`

1. **Create a Python virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure the GPU server IP:**
Edit `webcam_server.py` and update `GPU_SERVER_URL` if needed:
```python
GPU_SERVER_URL = "http://76.175.119.31:3005"
API_BASE_URL = "https://gpu.tailab42b6.ts.net"
```

4. **Run the webcam server:**
```bash
python webcam_server.py
```

The webcam server:
- Captures frames from the connected camera
- Detects faces locally using Haar Cascade
- Sends detected faces to the GPU server for recognition
- Authenticates with the API and calls `/api/checkoff/{name}` for recognized users
- Logs all attendance events to `attendance.log`

## Default Login

- **Email:** admin@scope.com
- **Password:** admin123

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user info

### Users
- `GET /api/users` - Get all users
- `POST /api/users` - Create new user (with profile pic upload)
- `GET /api/users/[userId]` - Get user with attendance record

### Attendance
- `GET /api/attendance/today` - Get today's present users
- `POST /api/checkoff/[userId]` - Check off a user for today

### Statistics
- `GET /api/stats` - Get attendance statistics

## Database Schema

### Users Table
- `id` (INTEGER PRIMARY KEY)
- `name` (TEXT NOT NULL)
- `email` (TEXT UNIQUE NOT NULL)
- `password_hash` (TEXT NOT NULL)
- `team` (TEXT)
- `major` (TEXT)
- `dob` (DATE)
- `graduating_class` (INTEGER)
- `profile_pic_path` (TEXT)
- `created_at` (DATETIME)

### Attendance Table
- `id` (INTEGER PRIMARY KEY)
- `user_id` (INTEGER NOT NULL)
- `date` (DATE NOT NULL)
- `checked_off_at` (DATETIME)
- UNIQUE(user_id, date)

### Sessions Table
- `id` (INTEGER PRIMARY KEY)
- `user_id` (INTEGER NOT NULL)
- `token` (TEXT UNIQUE NOT NULL)
- `created_at` (DATETIME)
- `expires_at` (DATETIME NOT NULL)

## Technologies

### Frontend & Backend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **SQLite** - Database (via better-sqlite3)
- **bcryptjs** - Password hashing
- **jsonwebtoken** - Authentication tokens
- **CSS Modules** - Component styling

### GPU Server (ML)
- **Python 3.8+**
- **Flask** - Web framework
- **face_recognition** - Face encoding library (dlib-based)
- **opencv-python** - Image processing
- **numpy** - Numerical computations

### RPi Client
- **Python 3.8+**
- **opencv-python** - Webcam capture and face detection
- **requests** - HTTP communication with GPU server and API

## External Libraries

### NPM Dependencies (Web Application)
- **next** - React framework with App Router and API routes
- **react** - UI library
- **typescript** - Type safety for JavaScript
- **better-sqlite3** - SQLite3 binding for Node.js
- **bcryptjs** - Password hashing and salting
- **jsonwebtoken** - JWT token creation and verification
- **multer** - Multipart form-data handling for file uploads
- **sharp** - Image processing and resizing

### Python Dependencies (GPU Server)
- **flask** - Web framework for building the REST API
- **face_recognition** - Face detection and encoding (wrapper around dlib)
- **dlib** - Machine learning library with deep learning models
- **opencv-python** - Computer vision library for image processing
- **numpy** - Numerical computing library
- **werkzeug** - WSGI utilities and file handling
- **Pillow** - Python Imaging Library for image operations

### Python Dependencies (RPi Client)
- **opencv-python** - Webcam capture and face detection using Haar Cascade
- **requests** - HTTP client library for API communication
- **numpy** - Numerical computing (required by opencv)

## Notes

- Profile pictures are stored in `public/uploads/`
- The database file (`database.db`) is created in the project root
- JWT tokens expire after 7 days
- Each user can only be checked off once per day
- Face encodings are pre-generated from training images in `gpu stuff/dataset/`
- RPi attends to 10-second cooldown per person to prevent duplicate check-ins
- GPU server supports both multipart form-data and base64 JSON image formats
- All timestamps are in ISO 8601 format with UTC timezone

