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
- `FIREBASE_*`: Firebase configuration (for future phases)

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
Returns service readiness status (currently placeholder until Firestore integration).

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

## 📈 Next Steps

### Phase 2: Database Integration
- Firestore client setup
- Student schema definition
- Readiness check with DB connectivity
- Repository pattern implementation

### Phase 3: Authentication
- Firebase Auth integration
- JWT token validation
- Role-based access control
- Protected endpoints

## 🤝 Contributing

1. Follow the established architecture patterns
2. Write tests for all new functionality
3. Update documentation for API changes
4. Ensure all tests pass before submitting PRs
