#!/usr/bin/env bash
set -euo pipefail

docker compose up -d --build
docker compose exec -T web python manage.py migrate --noinput
echo "Django app running on http://localhost:8000"