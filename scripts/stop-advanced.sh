#!/usr/bin/env bash
set -euo pipefail

echo "🛑 Stopping advanced Docker setup..."

# Stop and remove containers, networks, and volumes
docker compose -f docker-compose.full.yml down -v

echo "✅ Advanced setup stopped and cleaned up!"
