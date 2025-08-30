#!/bin/bash
set -e

echo "🔄 Starting development environment..."

# Ensure all services are running
echo "📡 Checking service health..."

# Check PostgreSQL
until PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U $POSTGRES_USER -d $POSTGRES_DB -c '\q' 2>/dev/null; do
  echo "Waiting for PostgreSQL..."
  sleep 2
done
echo "✅ PostgreSQL is ready!"

# Check Redis
until redis-cli -h redis ping | grep -q PONG; do
  echo "Waiting for Redis..."
  sleep 2
done
echo "✅ Redis is ready!"

# Check MinIO
until curl -f http://minio:9000/minio/health/live >/dev/null 2>&1; do
  echo "Waiting for MinIO..."
  sleep 2
done
echo "✅ MinIO is ready!"

# Run any pending migrations
echo "🔄 Checking for pending migrations..."
python manage.py migrate --noinput

echo "✨ All services are ready!"

# Run tests to verify setup
if [ -f .devcontainer/test-setup.sh ]; then
  echo ""
  bash .devcontainer/test-setup.sh
fi

echo ""
echo "🚀 Quick start guide:"
echo "   - Django app: http://localhost:8000"
echo "   - Admin panel: http://localhost:8000/admin"
echo "   - MinIO console: http://localhost:9001"
echo "   - API docs: http://localhost:8000/api/docs/"
echo ""
echo "📝 Default credentials:"
echo "   - Django admin: admin / admin123"
echo "   - MinIO: minioadmin / minioadmin"