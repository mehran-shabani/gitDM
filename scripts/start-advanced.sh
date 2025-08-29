#!/usr/bin/env bash
set -euo pipefail

docker compose up -d --build
docker compose exec -T web python manage.py migrate --noinput
echo "Advanced stack running: web:8000, db:5432, redis:6379, minio:9000 (console:9001)"
