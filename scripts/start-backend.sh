#!/usr/bin/env bash
set -euo pipefail

echo "🐍 Starting Django backend server (SQLite only)..."
echo "ℹ️  Note: Background tasks (Celery) are disabled in this simplified setup"

# Activate virtual environment if it exists
if [ -d "backend/venv" ]; then
  source backend/venv/bin/activate
fi

# Run migrations
echo "🔄 Running migrations..."
python manage.py migrate --noinput

# Start Django development server
echo "🚀 Starting Django server at http://localhost:8000"
python manage.py runserver 0.0.0.0:8000