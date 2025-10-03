#!/bin/bash

# UG Admin Development Server Startup Script
# This script starts both the backend (FastAPI) and frontend (React) servers

echo "🚀 Starting UG Admin Development Servers..."

# Add Poetry to PATH
export PATH="$HOME/.local/bin:$PATH"

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Stopping servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

# Start Backend (FastAPI)
echo "📡 Starting Backend (FastAPI) on http://localhost:8000..."
cd backend
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 2

# Start Frontend (React)
echo "🌐 Starting Frontend (React) on http://localhost:5173..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 3

echo ""
echo "✅ Both servers are starting up!"
echo ""
echo "📱 Frontend: http://localhost:5173 (or check terminal for actual port)"
echo "📡 Backend:  http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for background processes
wait $BACKEND_PID $FRONTEND_PID
