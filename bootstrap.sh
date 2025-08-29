#!/usr/bin/env bash
set -euo pipefail

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

# Start services
echo "Starting services with docker-compose ..."
docker compose up -d --build

# Apply migrations
echo "Applying migrations ..."
docker compose exec -T web python manage.py migrate --noinput

echo "All set. Web at: http://localhost:8000"