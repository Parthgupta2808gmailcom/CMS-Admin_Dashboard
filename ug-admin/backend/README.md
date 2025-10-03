# UG Admin Backend

Backend API for the Undergraduation.com Admin Dashboard built with FastAPI, following MVC/service-repository patterns with structured logging and comprehensive error handling.

## 🏗️ Architecture

The backend follows a clean architecture pattern with:

- **Core modules**: Configuration, logging, and error handling
- **API modules**: RESTful endpoints organized by version
- **Service layer**: Business logic (to be added in future phases)
- **Repository layer**: Data access (to be added in future phases)

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Poetry (for dependency management)

### Installation

```bash
# Install dependencies
poetry install

# Create environment file
cp .env.example .env
# Edit .env with your configuration
```

### Development Server

```bash
# Run development server with auto-reload
poetry run uvicorn app.main:app --reload

# Server will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

### Testing

```bash
# Run all tests
poetry run pytest

# Run tests with verbose output
poetry run pytest -v

# Run tests with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/api/test_health.py
```

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/v1/           # API endpoints (version 1)
│   │   ├── health.py     # Health check endpoints
│   │   └── __init__.py   # API router configuration
│   ├── core/             # Core application modules
│   │   ├── config.py     # Configuration management
│   │   ├── logging.py    # Structured logging
│   │   └── errors.py     # Error handling
│   ├── main.py           # FastAPI application
│   └── __init__.py
├── tests/                # Test modules
│   └── api/              # API tests
│       └── test_health.py
├── pyproject.toml        # Poetry configuration
└── README.md
```

## 🔧 Configuration

The application uses `pydantic-settings` for configuration management. Key settings:

- `ENV`: Environment (development, staging, production)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `ALLOWED_ORIGINS`: CORS allowed origins
- `FIREBASE_PROJECT_ID`: Firebase project ID
- `FIREBASE_PRIVATE_KEY_ID`: Firebase private key ID
- `FIREBASE_PRIVATE_KEY`: Firebase private key
- `FIREBASE_CLIENT_EMAIL`: Firebase client email
- `FIREBASE_CLIENT_ID`: Firebase client ID
- `FIREBASE_AUTH_URI`: Firebase auth URI
- `FIREBASE_TOKEN_URI`: Firebase token URI

## 🎯 **Phase 5: Advanced Features - COMPLETE!**

The backend now includes comprehensive advanced features for production-ready admissions management:

### ✅ **Implemented Features**

**🔍 Advanced Search & Filtering:**
- Multi-field search with full-text capabilities
- Faceted search with aggregated counts
- Search suggestions and autocomplete
- Complex filtering (status, country, date ranges)
- Efficient pagination and sorting

**📦 Bulk Operations:**
- CSV/JSON import with comprehensive validation
- Bulk export with filtering and field selection
- Row-by-row error reporting
- Processing time optimization
- Admin-only access controls

**📁 File Management:**
- Secure file uploads to Firebase Storage
- Multiple file types (transcripts, essays, portfolios)
- File validation and metadata tracking
- Storage usage analytics
- Audit trail for all file operations

**📧 Email Notifications:**
- Template-based email system
- Bulk email campaigns
- Delivery tracking and analytics
- Multiple provider support (mock, SendGrid, SES)
- Comprehensive audit logging

**📋 Audit Logging:**
- Complete compliance tracking
- User activity monitoring
- Structured log entries in Firestore
- Performance analytics
- Security event tracking

## 📊 Health Endpoints

### Liveness Probe
```bash
GET /api/v1/health/liveness
```
Returns service status to indicate if the service is running.

### Readiness Probe
```bash
GET /api/v1/health/readiness
```
Returns service readiness status with Firestore connectivity check. Returns `{"status": "up"}` if database is accessible, `{"status": "down"}` if not.

## 🧪 Testing

The test suite includes:

- **Health endpoint tests**: Verify liveness and readiness endpoints
- **Error handling tests**: Validate error response format
- **Async client tests**: Ensure async compatibility
- **Response validation**: Check JSON schema compliance

## 🔍 Logging

The application uses structured JSON logging with:

- **Request ID tracking**: Each request gets a unique identifier
- **Correlation**: Request IDs are included in all log entries
- **Structured data**: Logs include context and metadata
- **Error tracking**: Exceptions are logged with full context

## 🚨 Error Handling

All errors follow a consistent JSON contract:

```json
{
  "code": "VALIDATION|NOT_FOUND|AUTH|INTERNAL",
  "message": "Human readable error",
  "details": null,
  "requestId": "uuid-string"
}
```

## 🛠️ Development Tools

- **Ruff**: Fast Python linter
- **Black**: Code formatter
- **isort**: Import sorting
- **mypy**: Type checking
- **pytest**: Testing framework
- **httpx**: HTTP client for testing

## 🔥 Firestore Setup

### Prerequisites
- Firebase project with Firestore enabled
- Service account with Firestore permissions
- Google Cloud SDK (for local emulator)

### Environment Configuration

Create a `.env` file in the backend directory:

```env
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token

# Application Configuration
ENV=development
LOG_LEVEL=INFO
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
```

### Service Account Setup

1. **Create Service Account:**
   - Go to Firebase Console → Project Settings → Service Accounts
   - Click "Generate new private key"
   - Download the JSON file

2. **Set Environment Variables:**
   ```bash
   # Option 1: Use the JSON file directly
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   
   # Option 2: Set individual environment variables (recommended for production)
   # Copy values from the JSON file to your .env file
   ```

### Local Development with Emulator

For local development, you can use the Firestore emulator:

```bash
# Install Google Cloud SDK
# https://cloud.google.com/sdk/docs/install

# Start Firestore emulator
gcloud beta emulators firestore start --host-port=localhost:8080

# Set emulator environment variable
export FIRESTORE_EMULATOR_HOST=localhost:8080
```

### Production Deployment

For production, ensure your service account has the following roles:
- **Firebase Admin SDK Administrator Service Agent**
- **Cloud Datastore User** (for Firestore)

## 🎓 Student API Endpoints

The application provides comprehensive CRUD operations for student management with pagination, filtering, and validation.

### Base URL
All student endpoints are prefixed with `/api/v1/students`

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/students/` | Create a new student |
| GET | `/students/` | List students with pagination and filtering |
| GET | `/students/{id}` | Get a specific student by ID |
| PUT | `/students/{id}` | Update a student (partial updates allowed) |
| DELETE | `/students/{id}` | Delete a student |

### Create Student

**POST** `/api/v1/students/`

Create a new student record with validation.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "country": "USA",
  "grade": "12th",
  "application_status": "Exploring"
}
```

**Response (201 Created):**
```json
{
  "student": {
    "id": "generated-student-id",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "country": "USA",
    "grade": "12th",
    "application_status": "Exploring",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z",
    "last_active": "2023-01-01T00:00:00Z",
    "ai_summary": null
  },
  "message": "Student created successfully"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/students/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "country": "USA",
    "grade": "12th",
    "application_status": "Exploring"
  }'
```

### List Students

**GET** `/api/v1/students/`

Retrieve a paginated list of students with optional filtering.

**Query Parameters:**
- `page` (int, default: 1): Page number (1-based)
- `page_size` (int, default: 50, max: 100): Number of students per page
- `name` (string, optional): Filter by student name (partial match)
- `email` (string, optional): Filter by student email (partial match)
- `status` (string, optional): Filter by application status
- `order_by` (string, default: "created_at"): Field to order by
- `order_direction` (string, default: "desc"): Order direction ("asc" or "desc")

**Response (200 OK):**
```json
{
  "students": [
    {
      "id": "student-id-1",
      "name": "John Doe",
      "email": "john.doe@example.com",
      "phone": "+1234567890",
      "country": "USA",
      "grade": "12th",
      "application_status": "Exploring",
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z",
      "last_active": "2023-01-01T00:00:00Z",
      "ai_summary": null
    }
  ],
  "total_count": 1,
  "page": 1,
  "page_size": 50,
  "has_next": false,
  "message": "Retrieved 1 students"
}
```

**cURL Examples:**
```bash
# List all students
curl "http://localhost:8000/api/v1/students/"

# List with pagination
curl "http://localhost:8000/api/v1/students/?page=1&page_size=10"

# List with filters
curl "http://localhost:8000/api/v1/students/?name=John&status=Exploring&order_by=name&order_direction=asc"
```

### Get Student by ID

**GET** `/api/v1/students/{student_id}`

Retrieve a specific student by their unique identifier.

**Response (200 OK):**
```json
{
  "student": {
    "id": "student-id",
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "country": "USA",
    "grade": "12th",
    "application_status": "Exploring",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z",
    "last_active": "2023-01-01T00:00:00Z",
    "ai_summary": null
  },
  "message": "Student retrieved successfully"
}
```

**cURL Example:**
```bash
curl "http://localhost:8000/api/v1/students/student-id"
```

### Update Student

**PUT** `/api/v1/students/{student_id}`

Update a student record. Partial updates are allowed - only provide the fields you want to update.

**Request Body (partial update example):**
```json
{
  "name": "Jane Doe",
  "application_status": "Applying"
}
```

**Response (200 OK):**
```json
{
  "student": {
    "id": "student-id",
    "name": "Jane Doe",
    "email": "john.doe@example.com",
    "phone": "+1234567890",
    "country": "USA",
    "grade": "12th",
    "application_status": "Applying",
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T12:00:00Z",
    "last_active": "2023-01-01T12:00:00Z",
    "ai_summary": null
  },
  "message": "Student updated successfully"
}
```

**cURL Example:**
```bash
curl -X PUT "http://localhost:8000/api/v1/students/student-id" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "application_status": "Applying"
  }'
```

### Delete Student

**DELETE** `/api/v1/students/{student_id}`

Permanently delete a student record.

**Response (200 OK):**
```json
{
  "message": "Student deleted successfully",
  "student_id": "student-id"
}
```

**cURL Example:**
```bash
curl -X DELETE "http://localhost:8000/api/v1/students/student-id"
```

### Application Status Values

The `application_status` field accepts the following values:
- `"Exploring"` - Student is exploring options
- `"Shortlisting"` - Student is shortlisting universities
- `"Applying"` - Student is actively applying
- `"Submitted"` - Student has submitted applications

### Error Responses

All endpoints return consistent error responses:

**400 Bad Request (Validation Error):**
```json
{
  "detail": {
    "error": "Validation failed",
    "message": "Invalid email format",
    "details": {
      "field": "email",
      "value": "invalid-email"
    }
  }
}
```

**404 Not Found:**
```json
{
  "detail": {
    "error": "Student not found",
    "message": "Student with ID student-id does not exist",
    "student_id": "student-id"
  }
}
```

**500 Internal Server Error:**
```json
{
  "detail": {
    "error": "Internal server error",
    "message": "Failed to create student",
    "code": "INTERNAL"
  }
}
```

## 🔐 Authentication & Authorization

The application implements comprehensive Firebase Authentication with JWT token verification and role-based access control (RBAC).

### Authentication Flow

1. **Client Authentication**: Users authenticate via Firebase Auth (web/mobile)
2. **Token Verification**: API validates Firebase ID tokens using Firebase Admin SDK
3. **Role Assignment**: User roles are stored in Firestore `users` collection
4. **Access Control**: Endpoints enforce role-based permissions

### User Roles

| Role | Permissions |
|------|-------------|
| **Admin** | Full access: Create, Read, Update, Delete students |
| **Staff** | Limited access: Create, Read students (no Update/Delete) |

### Protected Endpoints

All `/api/v1/students/*` endpoints require authentication:

```http
Authorization: Bearer <firebase-id-token>
```

#### Role Requirements

| Endpoint | Method | Required Role | Description |
|----------|--------|---------------|-------------|
| `/students/` | POST | Staff or Admin | Create students |
| `/students/` | GET | Staff or Admin | List students |
| `/students/{id}` | GET | Staff or Admin | Get student by ID |
| `/students/{id}` | PUT | **Admin only** | Update student |
| `/students/{id}` | DELETE | **Admin only** | Delete student |

### Authentication Setup

#### 1. Firebase Project Configuration

Ensure your Firebase project has:
- **Authentication enabled** with desired sign-in methods
- **Firestore database** for user role management
- **Service Account** with Admin SDK privileges

#### 2. Environment Variables

Add Firebase Admin SDK credentials to `.env`:

```bash
# Firebase Admin SDK Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
```

#### 3. User Role Management

Users are automatically created in Firestore with default `staff` role:

```json
// Firestore: users/{uid}
{
  "role": "staff",
  "created_at": 1234567890,
  "last_login": 1234567890,
  "status": "active"
}
```

To promote a user to admin:

```javascript
// Update in Firestore Console or via Admin SDK
db.collection('users').doc(uid).update({
  role: 'admin',
  updated_at: Date.now()
});
```

### API Usage Examples

#### 1. Obtain Firebase ID Token (Client-side)

```javascript
// Web (Firebase SDK v9+)
import { getAuth, signInWithEmailAndPassword } from 'firebase/auth';

const auth = getAuth();
const userCredential = await signInWithEmailAndPassword(auth, email, password);
const idToken = await userCredential.user.getIdToken();
```

#### 2. Make Authenticated API Requests

```bash
# Create a student (Staff or Admin)
curl -X POST "http://localhost:8000/api/v1/students/" \
  -H "Authorization: Bearer <firebase-id-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "country": "USA",
    "application_status": "Exploring"
  }'

# Update a student (Admin only)
curl -X PUT "http://localhost:8000/api/v1/students/student-id" \
  -H "Authorization: Bearer <admin-firebase-id-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "application_status": "Applying"
  }'
```

#### 3. Handle Authentication Errors

```javascript
// Example error responses
{
  "detail": {
    "code": "AUTH",
    "message": "Authentication token has expired",
    "details": {...},
    "request_id": "uuid"
  }
}

{
  "detail": {
    "code": "FORBIDDEN", 
    "message": "Insufficient permissions. Required roles: ['admin']",
    "details": {
      "user_role": "staff",
      "required_roles": ["admin"]
    },
    "request_id": "uuid"
  }
}
```

### Security Features

- ✅ **JWT Token Validation**: Firebase Admin SDK verification
- ✅ **Role-Based Access Control**: Granular permissions per endpoint
- ✅ **Automatic User Creation**: Default role assignment for new users
- ✅ **Token Expiration Handling**: Proper error responses for expired tokens
- ✅ **Request Logging**: Comprehensive audit trail with user context
- ✅ **Error Consistency**: Standardized error response format

### Testing Authentication

Run authentication tests:

```bash
# Test authentication middleware
poetry run pytest tests/api/test_auth.py -v

# Test role-based access control
poetry run pytest tests/api/test_auth.py::TestRoleBasedAccessControl -v
```

### Troubleshooting

#### Common Issues

1. **"Firebase app does not exist"**
   - Ensure Firebase Admin SDK credentials are correctly set in `.env`
   - Verify `FIREBASE_PRIVATE_KEY` includes proper newlines

2. **"Invalid authentication token"**
   - Check token format: `Authorization: Bearer <token>`
   - Ensure token is not expired (Firebase tokens expire after 1 hour)
   - Verify token was issued by the correct Firebase project

3. **"Insufficient permissions"**
   - Check user role in Firestore `users/{uid}` document
   - Verify endpoint role requirements in API documentation

4. **"User not found in users collection"**
   - New users are auto-created with `staff` role
   - Check Firestore rules allow read/write to `users` collection

## 🔍 **Advanced Search API**

### Search Students
```bash
POST /api/v1/search/students
Authorization: Bearer <token>
Content-Type: application/json

{
  "text_query": "John Doe",
  "search_fields": ["name", "email"],
  "application_statuses": ["Exploring", "Shortlisting"],
  "countries": ["USA", "Canada"],
  "sort_field": "created_at",
  "sort_order": "desc",
  "limit": 50,
  "offset": 0
}
```

### Get Search Suggestions
```bash
GET /api/v1/search/suggestions?field=name&partial_value=John&limit=10
Authorization: Bearer <token>
```

### Get Search Facets
```bash
GET /api/v1/search/facets
Authorization: Bearer <token>
```

### Simple Search (Query Parameters)
```bash
GET /api/v1/search/students/simple?q=John&status=Exploring&country=USA&limit=20
Authorization: Bearer <token>
```

## 📦 **Bulk Operations API**

### Bulk Import Students
```bash
POST /api/v1/bulk/import
Authorization: Bearer <admin-token>
Content-Type: multipart/form-data

file: students.csv (or .json)
format_type: csv (optional, auto-detected)
validate_only: false (optional)
```

**CSV Format Example:**
```csv
name,email,country,application_status,phone,grade
John Doe,john@test.com,USA,Exploring,+1234567890,12
Jane Smith,jane@test.com,Canada,Shortlisting,,11
```

**JSON Format Example:**
```json
{
  "students": [
    {
      "name": "John Doe",
      "email": "john@test.com",
      "country": "USA",
      "application_status": "Exploring"
    }
  ]
}
```

### Export Students
```bash
GET /api/v1/bulk/export?format_type=csv&application_status=Exploring&country=USA
Authorization: Bearer <token>
```

**Export Parameters:**
- `format_type`: csv | json
- `application_status`: Filter by status
- `country`: Filter by country
- `start_date`: Filter by date (ISO format)
- `end_date`: Filter by date (ISO format)
- `include_fields`: Comma-separated field list

## 📁 **File Management API**

### Upload File for Student
```bash
POST /api/v1/files/students/{student_id}/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: transcript.pdf
file_type: transcript
description: "Official high school transcript"
```

**Supported File Types:**
- `transcript`: Academic transcripts
- `essay`: Application essays
- `recommendation`: Recommendation letters
- `portfolio`: Portfolio materials
- `certificate`: Certificates and awards
- `other`: Other documents

**Supported Formats:**
- PDF (.pdf)
- Word Documents (.doc, .docx)
- Images (.jpg, .jpeg, .png, .gif)
- Text Files (.txt)
- Excel Files (.xls, .xlsx)

### List Student Files
```bash
GET /api/v1/files/students/{student_id}?file_type=transcript
Authorization: Bearer <token>
```

### Get File Details
```bash
GET /api/v1/files/{file_id}
Authorization: Bearer <token>
```

### Delete File
```bash
DELETE /api/v1/files/{file_id}
Authorization: Bearer <token>
```

### Storage Statistics
```bash
GET /api/v1/files/storage/statistics
Authorization: Bearer <token>
```

## 📧 **Email Notifications API**

### Send Email to Recipients
```bash
POST /api/v1/notifications/send
Authorization: Bearer <token>
Content-Type: application/json

{
  "template": "welcome",
  "recipients": [
    {
      "email": "student@test.com",
      "name": "Student Name",
      "student_id": "student-123"
    }
  ],
  "template_data": {
    "welcome_message": "Welcome to our platform!"
  },
  "priority": "normal"
}
```

### Send Email to Specific Student
```bash
POST /api/v1/notifications/send-to-student
Authorization: Bearer <token>
Content-Type: application/json

{
  "student_id": "student-123",
  "template": "status_update",
  "template_data": {
    "new_status": "Shortlisting",
    "status_message": "Your application is being reviewed"
  }
}
```

### Send Bulk Emails
```bash
POST /api/v1/notifications/send-bulk
Authorization: Bearer <token>
Content-Type: application/json

{
  "student_ids": ["student-1", "student-2", "student-3"],
  "template": "application_reminder",
  "template_data": {
    "reminder_message": "Please complete your application"
  }
}
```

### Get Email Logs
```bash
GET /api/v1/notifications/logs?student_id=student-123&template=welcome&status=sent&limit=50
Authorization: Bearer <token>
```

**Available Email Templates:**
- `welcome`: Welcome new students
- `application_reminder`: Application status reminders
- `document_request`: Request specific documents
- `status_update`: Application status updates
- `followup`: General follow-up communications
- `interview_invitation`: Interview invitations
- `admission_decision`: Admission decisions

## 🔒 **Complete Role-Based Access Control**

| Endpoint | Admin | Staff | Description |
|----------|-------|-------|-------------|
| **Students** |
| `POST /students/` | ✅ | ✅ | Create student |
| `GET /students/` | ✅ | ✅ | List students |
| `GET /students/{id}` | ✅ | ✅ | Get student details |
| `PUT /students/{id}` | ✅ | ❌ | Update student |
| `DELETE /students/{id}` | ✅ | ❌ | Delete student |
| **Bulk Operations** |
| `POST /bulk/import` | ✅ | ❌ | Import students |
| `GET /bulk/export` | ✅ | ✅ | Export students |
| **Search** |
| `POST /search/students` | ✅ | ✅ | Search students |
| `GET /search/suggestions` | ✅ | ✅ | Search suggestions |
| `GET /search/facets` | ✅ | ✅ | Search facets |
| **Files** |
| `POST /files/students/{id}/upload` | ✅ | ✅ | Upload files |
| `GET /files/students/{id}` | ✅ | ✅ | List files |
| `GET /files/{id}` | ✅ | ✅ | Get file details |
| `DELETE /files/{id}` | ✅ | ✅ | Delete files |
| `GET /files/storage/statistics` | ✅ | ✅ | Storage stats |
| **Notifications** |
| `POST /notifications/send` | ✅ | ✅ | Send emails |
| `POST /notifications/send-to-student` | ✅ | ✅ | Send to student |
| `POST /notifications/send-bulk` | ✅ | ✅ | Send bulk emails |
| `GET /notifications/logs` | ✅ | ✅ | View email logs |

## 📋 **Comprehensive Audit Logging**

All critical actions are automatically logged for compliance:

**Logged Actions:**
- Student CRUD operations
- Bulk import/export operations
- File upload/download/delete
- Email sending activities
- User authentication events
- Search activities

**Audit Log Structure:**
```json
{
  "id": "audit-log-123",
  "user_id": "user-456",
  "user_email": "admin@test.com",
  "user_role": "admin",
  "action": "CREATE_STUDENT",
  "target_type": "student",
  "target_id": "student-789",
  "severity": "medium",
  "timestamp": "2025-01-01T12:00:00Z",
  "success": true,
  "details": {
    "student_name": "John Doe",
    "student_email": "john@test.com"
  },
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

## 🚀 **Production Deployment**

### Environment Variables
```bash
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token

# Application Configuration
ENV=production
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://yourdomain.com,https://admin.yourdomain.com

# Email Configuration (Optional)
DEFAULT_SENDER_EMAIL=noreply@yourdomain.com
DEFAULT_SENDER_NAME="Your Organization"
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry install --no-dev

COPY app/ ./app/
EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🧪 **Comprehensive Testing**

### Run All Tests
```bash
poetry run pytest -v
```

### Test Coverage
```bash
poetry run pytest --cov=app --cov-report=html
```

### Test Categories
```bash
# API Tests
poetry run pytest tests/api/ -v

# Authentication Tests
poetry run pytest tests/api/test_auth.py -v

# Bulk Operations Tests
poetry run pytest tests/api/test_bulk_operations.py -v

# Search Tests
poetry run pytest tests/api/test_search.py -v

# File Management Tests
poetry run pytest tests/api/test_files.py -v

# Notification Tests
poetry run pytest tests/api/test_notifications.py -v
```


## 🤝 Contributing

1. Follow the established architecture patterns
2. Write tests for all new functionality
3. Update documentation for API changes
4. Ensure all tests pass before submitting PRs

The backend provides a solid foundation for a comprehensive admissions management system! 🚀


