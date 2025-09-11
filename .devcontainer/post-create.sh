#!/bin/bash
set -e

echo "🚀 Setting up GitHub Codespaces development environment..."

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from .env.example..."
    cp .env.example .env
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r backend/requirements.txt

# Install Node.js dependencies for frontend
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
cd ..

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
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

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Build frontend
echo "🏗️ Building frontend..."
cd frontend
npm run build
cd ..

echo "✨ Development environment setup complete!"
echo ""
echo "🌐 Available services:"
echo "  - Django backend: http://localhost:8000"
echo "  - React frontend: http://localhost:3000 (use ./scripts/start-frontend.sh)"
echo "  - Admin panel: http://localhost:8000/admin"
echo ""
echo "🔐 Default credentials:"
echo "  - Django admin: admin / admin123"
echo ""
echo "🚀 Quick start:"
echo "  - Start backend: python manage.py runserver 0.0.0.0:8000"
echo "  - Start frontend: cd frontend && npm run dev"
echo "  - Start both: ./scripts/start-dev.sh"