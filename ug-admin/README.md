# Undergraduation.com Admin Dashboard

A modern admin dashboard for managing Undergraduation.com platform, built with FastAPI and React.

## 🏗️ Architecture

This is a monorepo containing:

- **Backend**: FastAPI (Python) with Firebase Admin SDK and Firestore
- **Frontend**: React 18 with Vite, TypeScript, MUI, and Firebase SDK
- **Authentication**: Firebase Auth (Email/Password + Google)

## 📋 Prerequisites

- **Python 3.11+** with Poetry
- **Node.js 18+** with npm
- **Firebase project** with Firestore enabled
- **Firebase project** with Authentication enabled

## 🚀 Quick Start

### Backend Setup

```bash
cd backend

# Install dependencies
poetry install

# Create .env file with Firebase credentials
cp .env.example .env
# Edit .env with your Firebase service account key

# Run development server
poetry run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file with Firebase config
cp .env.example .env.local
# Edit .env.local with your Firebase config

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 🛠️ Development

### Backend Development

```bash
cd backend

# Run tests
poetry run pytest

# Format code
poetry run black .
poetry run isort .

# Lint code
poetry run ruff check .
poetry run mypy .
```

### Frontend Development

```bash
cd frontend

# Run tests
npm run test

# Run tests in watch mode
npm run test:watch

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
ug-admin/
├── backend/                 # FastAPI backend
│   ├── app/                # Application code
│   ├── tests/              # Test files
│   ├── pyproject.toml      # Poetry dependencies
│   └── README.md           # Backend documentation
├── frontend/               # React frontend
│   ├── src/                # Source code
│   ├── public/             # Static assets
│   ├── package.json        # npm dependencies
│   └── README.md           # Frontend documentation
├── docs/                   # Project documentation
├── .gitignore             # Git ignore rules
├── .editorconfig          # Editor configuration
└── README.md              # This file
```

## 🔧 Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Uvicorn** - ASGI server
- **Poetry** - Dependency management
- **Firebase Admin SDK** - Firebase integration
- **Firestore** - NoSQL database
- **Pydantic** - Data validation
- **pytest** - Testing framework

### Frontend
- **React 18** - UI library
- **Vite** - Build tool and dev server
- **TypeScript** - Type safety
- **Material-UI (MUI)** - Component library
- **React Router** - Client-side routing
- **TanStack Query** - Data fetching
- **Firebase SDK** - Firebase integration
- **Vitest** - Testing framework

### Development Tools
- **Ruff** - Python linter
- **Black** - Python formatter
- **isort** - Import sorting
- **mypy** - Type checking
- **ESLint** - JavaScript linter
- **Prettier** - Code formatter

## 🔐 Environment Variables

### Backend (.env)
```env
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=your-service-account@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
```

### Frontend (.env.local)
```env
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your-project-id
VITE_FIREBASE_STORAGE_BUCKET=your-project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
```

## 📚 Development Phases

### Phase 1: Foundation ✅
- [x] Monorepo structure setup
- [x] Backend boilerplate with Poetry
- [x] Frontend boilerplate with Vite + React + TypeScript
- [x] Core dependencies installation
- [x] Development tooling configuration

### Phase 2: Authentication ✅
- [x] Firebase Auth integration
- [x] Protected routes
- [x] User management
- [x] Role-based access control

### Phase 3: Core Features ✅
- [x] Dashboard overview
- [x] User management
- [x] Content management
- [x] Analytics and reporting

### Phase 4: Advanced Features (Planned)
- [x] Real-time notifications
- [ ] Advanced analytics
- [x] Export/import functionality
- [x] API documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is proprietary software for Undergraduation.com
