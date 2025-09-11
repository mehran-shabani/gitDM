#!/usr/bin/env bash
set -euo pipefail

echo "🌐 Starting React frontend server..."

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  echo "📦 Installing dependencies..."
  npm install
fi

# Start Vite development server
echo "🚀 Starting frontend server at http://localhost:3000"
npm run dev -- --host 0.0.0.0 --port 3000