#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting full development environment..."

# Function to kill background processes on exit
cleanup() {
  echo "🛑 Stopping development servers..."
  jobs -p | xargs -r kill
  exit 0
}

trap cleanup EXIT

# Start backend in background
echo "🐍 Starting backend server..."
./scripts/start-backend.sh &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend in background
echo "🌐 Starting frontend server..."
./scripts/start-frontend.sh &
FRONTEND_PID=$!

echo ""
echo "✅ Development servers started!"
echo "🌐 Frontend: http://localhost:3000"
echo "🐍 Backend:  http://localhost:8000"
echo "🔐 Admin:    http://localhost:8000/admin"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID