#!/usr/bin/env bash
set -euo pipefail

echo "🛑 Stopping simple Docker setup..."

# Stop and remove containers, networks, and volumes
docker compose -f docker-compose.simple.yml down -v

echo "✅ Simple setup stopped and cleaned up!"
