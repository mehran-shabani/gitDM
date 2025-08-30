#!/bin/bash
set -e

echo "🚀 Setting up development environment..."

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📋 Creating .env file from .env.example..."
    cp .env.example .env
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U $POSTGRES_USER -d $POSTGRES_DB -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✅ PostgreSQL is ready!"

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

echo "✨ Development environment setup complete!"
echo "🌐 Django app will be available at: http://localhost:8000"
echo "🔐 Admin panel: http://localhost:8000/admin (username: admin, password: admin123)"
echo "🗄️ MinIO console: http://localhost:9001 (username: minioadmin, password: minioadmin)"