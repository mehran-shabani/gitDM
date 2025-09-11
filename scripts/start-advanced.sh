#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting advanced Docker setup (with PostgreSQL and Redis)..."

# Create .env from .env.example if it doesn't exist
if [ ! -f .env ]; then
  echo "📋 Creating .env file from .env.example..."
  cp .env.example .env
fi

# Use the full docker-compose configuration
echo "🐳 Starting all services..."
docker compose -f docker-compose.full.yml up -d --build

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
until docker compose -f docker-compose.full.yml exec -T db pg_isready -U postgres >/dev/null 2>&1; do
  echo "Database is not ready - sleeping..."
  sleep 2
done

# Run migrations
echo "🔄 Running migrations..."
docker compose -f docker-compose.full.yml exec -T backend python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "👤 Creating superuser..."
docker compose -f docker-compose.full.yml exec -T backend python manage.py shell << EOF
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
docker compose -f docker-compose.full.yml exec -T backend python manage.py collectstatic --noinput

echo ""
echo "✅ Advanced setup complete!"
echo "🌐 Frontend: http://localhost:3000"
echo "🐍 Backend:  http://localhost:8000"
echo "🔐 Admin:    http://localhost:8000/admin (admin/admin123)"
echo "🐘 PostgreSQL: localhost:5432"
echo "🔴 Redis: localhost:6379"
echo ""
echo "📊 View logs: docker compose -f docker-compose.full.yml logs -f"
echo "🛑 Stop services: ./scripts/stop-advanced.sh"