#!/bin/bash

# Script to switch between simple and full mode
# Usage: ./switch_mode.sh simple|full

MODE=${1:-simple}

if [ "$MODE" != "simple" ] && [ "$MODE" != "full" ]; then
    echo "Usage: $0 {simple|full}"
    echo "  simple: SQLite + Django cache + Django storage"
    echo "  full:   PostgreSQL + Redis + MinIO"
    exit 1
fi

# Update .env file
if [ -f .env ]; then
    sed -i "s/^SETTINGS_MODE=.*/SETTINGS_MODE=$MODE/" .env
    sed -i "s/^COMPOSE_MODE=.*/COMPOSE_MODE=$MODE/" .env
else
    echo "SETTINGS_MODE=$MODE" > .env
    echo "COMPOSE_MODE=$MODE" >> .env
fi

echo "✅ Switched to $MODE mode"
echo "📁 Settings: config.${MODE}_settings.py"

if [ "$MODE" = "simple" ]; then
    echo "🗄️  Database: SQLite (db.sqlite3)"
    echo "💾 Cache: Django LocMem"
    echo "📁 Storage: Django FileSystemStorage"
    echo "🐳 Docker: docker-compose.simple.yml"
    echo ""
    echo "Run with:"
    echo "  python manage.py runserver"
    echo "  # or"
    echo "  docker-compose -f docker-compose.simple.yml up"
else
    echo "🗄️  Database: PostgreSQL"
    echo "💾 Cache: Redis"
    echo "📁 Storage: MinIO"
    echo "🐳 Docker: docker-compose.yml"
    echo ""
    echo "Run with:"
    echo "  python manage.py runserver"
    echo "  # or" 
    echo "  docker-compose up"
fi