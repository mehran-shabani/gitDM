#!/usr/bin/env bash
set -euo pipefail

cd /app

if [ ! -f .env ]; then
  echo "Creating .env for Codespaces..."
  cat > .env <<'ENV'
DJANGO_SECRET_KEY=dev-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,.app.github.dev,.github.dev

USE_SQLITE=False
POSTGRES_DB=appdb
POSTGRES_USER=appuser
POSTGRES_PASSWORD=apppass
POSTGRES_HOST=db
POSTGRES_PORT=5432

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

USE_MINIO=True
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_USE_HTTPS=False
MINIO_MEDIA_BUCKET=media
MINIO_STATIC_BUCKET=static

# Optional
# GAPGPT_API_KEY=
# OPENAI_API_KEY=
ENV
fi

python -V || true

# Apply migrations and collect static (entrypoint also does this, but running once here is fine)
python manage.py migrate --noinput || true
python manage.py collectstatic --noinput || true

echo "Codespaces post-create completed. Open port 8000 to access the app."

