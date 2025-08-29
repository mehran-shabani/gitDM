#!/usr/bin/env bash
set -euo pipefail

docker compose -f docker-compose.simple.yml up -d --build
docker compose -f docker-compose.simple.yml exec -T web python manage.py migrate --noinput
echo "Simple stack running at http://localhost:8000"
