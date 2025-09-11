#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Setting up development environment for GitDM (SQLite only)..."
echo "ℹ️  Note: This setup uses SQLite and disables background tasks for simplicity"

# Create .env from .env.example if it doesn't exist
if [ ! -f .env ]; then
  echo "📋 Creating .env file from .env.example..."
  cp .env.example .env
fi

# Backend setup
echo "🐍 Setting up backend (Django with SQLite)..."
if [ ! -d "backend/venv" ]; then
  echo "📦 Creating Python virtual environment..."
  python -m venv backend/venv
fi

echo "📦 Installing Python dependencies..."
source backend/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r backend/requirements.txt

echo "🔄 Running database migrations..."
python manage.py migrate

echo "👤 Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Superuser created successfully!")
else:
    print("Superuser already exists.")
EOF

echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

deactivate

# Frontend setup
echo "🌐 Setting up frontend (React)..."
cd frontend

if [ ! -d "node_modules" ]; then
  echo "📦 Installing Node.js dependencies..."
  npm install
fi

echo "🔧 Building frontend..."
npm run build

cd ..

echo "✅ Development environment setup complete!"
echo ""
echo "🚀 To start development servers:"
echo "  Backend:  ./scripts/start-backend.sh"
echo "  Frontend: ./scripts/start-frontend.sh"
echo "  Both:     ./scripts/start-dev.sh"
echo ""
echo "🌐 URLs:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "  Admin:    http://localhost:8000/admin (admin/admin123)"
echo ""
echo "ℹ️  Note: Background tasks (Celery) are disabled in this simplified setup"