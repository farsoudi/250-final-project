# Scope Attendance API Documentation

**Base URL:** `https://gpu.tailab42b6.ts.net`

## Authentication

The API uses token-based authentication. Most endpoints require a valid JWT token in the `Authorization` header.

**Format:** `Authorization: Bearer <token>`

Tokens expire after 7 days.

---

## Endpoints

### Authentication

#### Login
Authenticate a user and receive an access token.

**Endpoint:** `POST /api/auth/login`

**Authentication:** Not required

**Request Body:**
{
  "email": "string",
  "password": "string"
}**Response (200 OK):**
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "team": "Frontend",
    "major": "Computer Science",
    "graduating_class": 2024,
    "profile_pic_path": "/uploads/1234567890-profile.jpg"
  }
}**Error Responses:**
- `400 Bad Request` - Missing email or password
- `401 Unauthorized` - Invalid credentials

**Example:**
curl -X POST https://gpu.tailab42b6.ts.net/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@scope.com",
    "password": "admin123"
  }'---

#### Get Current User
Get information about the currently authenticated user.

**Endpoint:** `GET /api/auth/me`

**Authentication:** Required

**Response (200 OK):**
{
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "team": "Frontend",
    "major": "Computer Science",
    "dob": "2000-01-15",
    "graduating_class": 2024,
    "profile_pic_path": "/uploads/1234567890-profile.jpg"
  }
}**Error Responses:**
- `401 Unauthorized` - Invalid or missing token
- `404 Not Found` - User not found

**Example:**
curl -X GET https://gpu.tailab42b6.ts.net/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"---

### Users

#### Get All Users
Retrieve a list of all users in the system.

**Endpoint:** `GET /api/users`

**Authentication:** Required

**Response (200 OK):**
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "team": "Frontend",
      "major": "Computer Science",
      "dob": "2000-01-15",
      "graduating_class": 2024,
      "profile_pic_path": "/uploads/1234567890-profile.jpg"
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "team": "Backend",
      "major": "Computer Science",
      "dob": "2001-05-20",
      "graduating_class": 2025,
      "profile_pic_path": null
    }
  ]
}**Error Responses:**
- `401 Unauthorized` - Invalid or missing token

**Example:**
curl -X GET https://gpu.tailab42b6.ts.net/api/users \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"---

#### Create User
Create a new user account.

**Endpoint:** `POST /api/users`

**Authentication:** Required

**Request Body:** (multipart/form-data)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | User's full name |
| `email` | string | Yes | User's email address (must be unique) |
| `password` | string | Yes | User's password |
| `team` | string | No | User's team name (max 255 characters) |
| `major` | string | No | User's major |
| `dob` | string | No | Date of birth (YYYY-MM-DD format) |
| `graduating_class` | integer | No | Graduating year |
| `profile_pic` | file | No | Profile picture image file |

**Response (200 OK):**
{
  "message": "User created successfully",
  "userId": 3
}**Error Responses:**
- `400 Bad Request` - Missing required fields, name already exists, or email already exists
- `401 Unauthorized` - Invalid or missing token

**Note:** User names must be unique. If a name already exists, the request will fail with a 400 error.

**Example (without profile picture):**
curl -X POST https://gpu.tailab42b6.ts.net/api/users \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "name=John Doe" \
  -F "email=john@example.com" \
  -F "password=securepassword123" \
  -F "team=Frontend" \
  -F "major=Computer Science" \
  -F "dob=2000-01-15" \
  -F "graduating_class=2024"**Example (with profile picture):**
curl -X POST https://gpu.tailab42b6.ts.net/api/users \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "name=Jane Smith" \
  -F "email=jane@example.com" \
  -F "password=securepassword123" \
  -F "team=Backend" \
  -F "major=Computer Science" \
  -F "dob=2001-05-20" \
  -F "graduating_class=2025" \
  -F "profile_pic=@/path/to/image.jpg"---

#### Get User by Name
Get detailed information about a specific user, including their attendance record.

**Endpoint:** `GET /api/users/{name}`

**Authentication:** Required

**Path Parameters:**
- `name` (string, required) - The name of the user (URL encoded)

**Response (200 OK):**
{
  "user": {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "team": "Frontend",
    "major": "Computer Science",
    "dob": "2000-01-15",
    "graduating_class": 2024,
    "profile_pic_path": "/uploads/1234567890-profile.jpg"
  },
  "attendance": [
    {
      "date": "2024-01-15",
      "checked_off_at": "2024-01-15T10:30:00.000Z"
    },
    {
      "date": "2024-01-14",
      "checked_off_at": "2024-01-14T09:15:00.000Z"
    }
  ]
}**Error Responses:**
- `400 Bad Request` - Invalid user name
- `401 Unauthorized` - Invalid or missing token
- `404 Not Found` - User not found

**Example:**
curl -X GET "https://gpu.tailab42b6.ts.net/api/users/John%20Doe" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

**Note:** The name must be URL encoded. For example, "John Doe" becomes "John%20Doe".---

### Attendance

#### Check Off User
Mark a user as present for today. Each user can only be checked off once per day.

**Endpoint:** `POST /api/checkoff/{name}`

**Authentication:** Required

**Path Parameters:**
- `name` (string, required) - The name of the user to check off (URL encoded)

**Response (200 OK):**
{
  "message": "User checked off successfully",
  "name": "John Doe",
  "date": "2024-01-15"
}

**Error Responses:**
- `400 Bad Request` - Invalid user name or user already checked off today
- `401 Unauthorized` - Invalid or missing token
- `404 Not Found` - User not found

**Example:**
curl -X POST "https://gpu.tailab42b6.ts.net/api/checkoff/John%20Doe" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

**Note:** The name must be URL encoded. For example, "John Doe" becomes "John%20Doe".

---

#### Uncheck Off User
Remove a user's attendance record for today. This allows reverting a checkoff if it was done by mistake.

**Endpoint:** `DELETE /api/checkoff/{name}`

**Authentication:** Required

**Path Parameters:**
- `name` (string, required) - The name of the user to uncheck off (URL encoded)

**Response (200 OK):**
{
  "message": "User uncheckoff successfully",
  "name": "John Doe",
  "date": "2024-01-15"
}

**Error Responses:**
- `400 Bad Request` - Invalid user name or user is not checked off today
- `401 Unauthorized` - Invalid or missing token
- `404 Not Found` - User not found

**Example:**
curl -X DELETE "https://gpu.tailab42b6.ts.net/api/checkoff/John%20Doe" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

**Note:** The name must be URL encoded. For example, "John Doe" becomes "John%20Doe".

---

#### Get Today's Attendance
Get a list of all users who have been checked off today.

**Endpoint:** `GET /api/attendance/today`

**Authentication:** Required

**Response (200 OK):**
{
  "users": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "team": "Frontend",
      "major": "Computer Science",
      "graduating_class": 2024,
      "profile_pic_path": "/uploads/1234567890-profile.jpg",
      "checked_off_at": "2024-01-15T10:30:00.000Z"
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "team": "Backend",
      "major": "Computer Science",
      "graduating_class": 2025,
      "profile_pic_path": null,
      "checked_off_at": "2024-01-15T09:15:00.000Z"
    }
  ],
  "date": "2024-01-15"
}**Error Responses:**
- `401 Unauthorized` - Invalid or missing token

**Example:**sh
curl -X GET https://gpu.tailab42b6.ts.net/api/attendance/today \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"---

### Statistics

#### Get Statistics
Get comprehensive attendance statistics including totals, breakdowns by team and graduating class, and most active users.

**Endpoint:** `GET /api/stats`

**Authentication:** Required

**Response (200 OK):**
{
  "totalUsers": 50,
  "todayAttendance": 35,
  "attendanceByTeam": [
    {
      "team": "Frontend",
      "user_count": 15,
      "attendance_count": 120
    },
    {
      "team": "Backend",
      "user_count": 12,
      "attendance_count": 95
    }
  ],
  "attendanceByClass": [
    {
      "graduating_class": 2024,
      "user_count": 20,
      "attendance_count": 150
    },
    {
      "graduating_class": 2025,
      "user_count": 18,
      "attendance_count": 130
    }
  ],
  "mostActiveUsers": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "team": "Frontend",
      "attendance_count": 45
    },
    {
      "id": 2,
      "name": "Jane Smith",
      "email": "jane@example.com",
      "team": "Backend",
      "attendance_count": 42
    }
  ]
}**Error Responses:**
- `401 Unauthorized` - Invalid or missing token

**Example:**
curl -X GET https://gpu.tailab42b6.ts.net/api/stats \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"---

## Error Responses

All error responses follow this format:

{
  "error": "Error message description"
}
### HTTP Status Codes

- `200 OK` - Request successful
- `400 Bad Request` - Invalid request parameters or data
- `401 Unauthorized` - Authentication required or invalid token
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## Data Models

### User Object
{
  id: number;
  name: string;
  email: string;
  team: string | null;
  major: string | null;
  dob: string | null; // YYYY-MM-DD format
  graduating_class: number | null;
  profile_pic_path: string | null; // URL path to profile picture
}### Attendance Recordypescript
{
  date: string; // YYYY-MM-DD format
  checked_off_at: string; // ISO 8601 datetime string
}### Team Statisticsescript
{
  team: string;
  user_count: number;
  attendance_count: number;
}### Class Statisticsypescript
{
  graduating_class: number;
  user_count: number;
  attendance_count: number;
}---

## Notes

- All dates are in UTC timezone
- Profile pictures are stored at `/uploads/{filename}` and accessible via the base URL
- Each user can only be checked off once per day
- Tokens expire after 7 days
- Email addresses must be unique across all users
- The `team` field has a maximum length of 255 characters