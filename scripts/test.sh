#!/usr/bin/env bash
set -euo pipefail

echo "🧪 Running all tests..."

# Backend tests
echo "🐍 Running backend tests..."
if [ -d "backend/venv" ]; then
  source backend/venv/bin/activate
fi

echo "Running pytest..."
pytest -v --tb=short

if [ -d "backend/venv" ]; then
  deactivate
fi

# Frontend tests
echo "🌐 Running frontend tests..."
cd frontend

if [ -f "package.json" ]; then
  echo "Running frontend linting..."
  npm run lint
  
  echo "Building frontend..."
  npm run build
  
  # Add frontend tests here when they exist
  # echo "Running frontend unit tests..."
  # npm run test
fi

cd ..

echo "✅ All tests completed successfully!"