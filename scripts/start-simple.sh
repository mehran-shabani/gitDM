#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting simple Docker setup (SQLite database only)..."
echo "ℹ️  Note: Background tasks (Celery) are disabled in this simplified setup"

# Create .env from .env.example if it doesn't exist
if [ ! -f .env ]; then
  echo "📋 Creating .env file from .env.example..."
  cp .env.example .env
fi

# Start simple Docker setup
echo "🐳 Starting Django service..."
docker compose -f docker-compose.simple.yml up -d --build

# Wait for web service to be ready
echo "⏳ Waiting for web service to be ready..."
until docker compose -f docker-compose.simple.yml exec -T web python -c "import sys; print(sys.version)" >/dev/null 2>&1; do
  echo "Web service is not ready - sleeping..."
  sleep 2
done

# Run migrations
echo "🔄 Running migrations..."
docker compose -f docker-compose.simple.yml exec -T web python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "👤 Creating superuser..."
docker compose -f docker-compose.simple.yml exec -T web python manage.py shell << EOF
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
docker compose -f docker-compose.simple.yml exec -T web python manage.py collectstatic --noinput

echo ""
echo "✅ Simple setup complete!"
echo "🐍 Django app: http://localhost:8000"
echo "🔐 Admin panel: http://localhost:8000/admin (admin/admin123)"
echo ""
echo "📊 View logs: docker compose -f docker-compose.simple.yml logs -f"
echo "🛑 Stop services: ./scripts/stop-simple.sh"
echo "ℹ️  Note: Background tasks (Celery) are disabled in this simplified setup"
