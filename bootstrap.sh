#!/usr/bin/env bash
set -euo pipefail

# Create .env from .env.example if it doesn't exist
if [ ! -f .env ]; then
  echo "📋 Creating .env file from .env.example..."
  cp .env.example .env
fi

# Load .env if present
if [ -f .env ]; then
  set -a
  # best-effort load; ignore comments/empty lines
  while IFS='=' read -r key value; do
    if [[ -z "$key" ]] || [[ "$key" =~ ^# ]]; then continue; fi
    export "$key"="${value}"
  done < <(grep -v '^#' .env | sed '/^$/d')
  set +a
fi

# Check if we're in GitHub Codespaces
if [ -n "${CODESPACES:-}" ]; then
  echo "🚀 Detected GitHub Codespaces environment"
  # Update ALLOWED_HOSTS in .env for Codespaces
  sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=localhost,127.0.0.1,*.githubpreview.dev,*.app.github.dev,${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/" .env
fi

# Start services
echo "Starting services with docker-compose ..."
docker compose up -d --build

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
until docker compose exec -T db pg_isready -U ${POSTGRES_USER:-appuser} >/dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done
echo "✅ PostgreSQL is ready!"

# Apply migrations
echo "🔄 Applying migrations ..."
docker compose exec -T web python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "👤 Creating superuser..."
docker compose exec -T web python manage.py shell << EOF
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
docker compose exec -T web python manage.py collectstatic --noinput

echo "✨ All set!"
echo "🌐 Django app: http://localhost:8000"
echo "🔐 Admin panel: http://localhost:8000/admin (username: admin, password: admin123)"
echo "🗄️ MinIO console: http://localhost:9001 (username: minioadmin, password: minioadmin)"

if [ -n "${CODESPACES:-}" ]; then
  echo ""
  echo "📌 In GitHub Codespaces, your app is available at:"
  echo "   https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
fi