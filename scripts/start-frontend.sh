#!/usr/bin/env bash
set -euo pipefail

echo "🌐 Starting React frontend server..."

# Change to frontend directory
cd frontend

# Check if .env file exists, create from template if not
if [ ! -f ".env" ]; then
  echo "📋 Creating .env file..."
  cat > .env << EOF
# Frontend Environment Configuration
# Simplified setup for development with local backend

# API Configuration
VITE_API_BASE_URL=http://localhost:8000/api
VITE_API_WITH_CREDENTIALS=false

# Development Configuration
VITE_DEV_MODE=true
EOF
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo "📦 Installing dependencies..."
  npm install
fi

# Check if backend is running
if ! curl -s http://localhost:8000/api/ > /dev/null 2>&1; then
  echo "⚠️  Warning: Backend server not detected at http://localhost:8000"
  echo "   Make sure to start the backend first with: ./scripts/start-backend.sh"
  echo ""
fi

# Start Vite development server
echo "🚀 Starting frontend server at http://localhost:3000"
echo "   Backend API: http://localhost:8000/api"
echo "   Press Ctrl+C to stop"
echo ""
npm run dev -- --host 0.0.0.0 --port 3000