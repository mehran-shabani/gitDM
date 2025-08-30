#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Starting GitDM application in GitHub Codespace..."

# Start PostgreSQL
echo "📊 Starting PostgreSQL..."
sudo -u postgres pg_ctlcluster 17 main start

# Start Redis
echo "🔴 Starting Redis..."
sudo redis-server --daemonize yes

# Start MinIO
echo "📦 Starting MinIO..."
mkdir -p /tmp/minio-data
MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin nohup minio server /tmp/minio-data --console-address ":9001" > /tmp/minio.log 2>&1 &

# Wait a moment for services to start
sleep 3

# Setup MinIO buckets
echo "🪣 Setting up MinIO buckets..."
mc alias set local http://localhost:9000 minioadmin minioadmin > /dev/null 2>&1
mc mb local/media local/static > /dev/null 2>&1 || echo "Buckets may already exist"

# Activate virtual environment and run Django
echo "🐍 Activating Python environment..."
source venv/bin/activate

# Run migrations
echo "📋 Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "👤 Setting up admin user..."
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin@example.com', 'admin123', full_name='Admin User') if not User.objects.filter(email='admin@example.com').exists() else print('Admin user already exists')" | python manage.py shell

# Start Django development server
echo "🌟 Starting Django development server..."
echo ""
echo "✅ Application is ready!"
echo "📍 Health check: http://localhost:8000/health/"
echo "📚 API docs: http://localhost:8000/api/docs/"
echo "🔧 Admin panel: http://localhost:8000/admin/"
echo "🔑 Admin credentials: admin@example.com / admin123"
echo "📦 MinIO console: http://localhost:9001/ (minioadmin / minioadmin)"
echo ""

python manage.py runserver 0.0.0.0:8000