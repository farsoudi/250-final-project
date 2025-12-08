# Scope Attendance

A full-stack attendance tracking application for Scope CS Club built with Next.js, SQLite, and TypeScript.

## Features

- 🔐 **Authentication**: Token-based login system
- 📊 **Dashboard**: View all users and mark attendance for today
- 👤 **User Management**: Add new users with profile information
- 📈 **Statistics**: View attendance by team, graduating class, and most active users
- 📝 **User Profiles**: Individual attendance records for each user
- 🎨 **Modern UI**: Polished interface with Scope branding

## Setup

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

## Project Structure

```
├── app/
│   ├── api/              # API routes
│   ├── components/       # React components
│   ├── login/           # Login page
│   ├── add-user/        # Add user page
│   ├── user/[userId]/   # User profile page
│   ├── stats/           # Statistics page
│   └── page.tsx         # Dashboard (home)
├── lib/                 # Utility functions
├── public/
│   ├── images/          # Static images (Scope logo)
│   └── uploads/         # Uploaded profile pictures
├── scripts/
│   └── init-db.js       # Database initialization
└── database.db          # SQLite database (created after init)
```

## Technologies

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **SQLite** - Database (via better-sqlite3)
- **bcryptjs** - Password hashing
- **jsonwebtoken** - Authentication tokens
- **CSS Modules** - Component styling

## Notes

- Profile pictures are stored in `public/uploads/`
- The database file (`database.db`) is created in the project root
- JWT tokens expire after 7 days
- Each user can only be checked off once per day

