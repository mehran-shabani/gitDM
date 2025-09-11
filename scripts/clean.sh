#!/usr/bin/env bash
set -euo pipefail

echo "🧹 Cleaning up project artifacts..."

# Clean Python artifacts
echo "🐍 Cleaning Python artifacts..."
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

# Clean frontend artifacts
if [ -d "frontend" ]; then
    echo "🌐 Cleaning frontend artifacts..."
    cd frontend
    if [ -d "dist" ]; then
        rm -rf dist
    fi
    if [ -d "node_modules/.cache" ]; then
        rm -rf node_modules/.cache
    fi
    cd ..
fi

# Clean Docker artifacts (optional)
read -p "🐳 Clean Docker artifacts? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🐳 Cleaning Docker artifacts..."
    docker system prune -f
    docker volume prune -f
fi

# Clean database (optional)
read -p "🗄️ Reset SQLite database? This will delete all data! (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗄️ Removing SQLite database..."
    if [ -f "db.sqlite3" ]; then
        rm db.sqlite3
        echo "Database removed. Run migrations to recreate."
    else
        echo "No SQLite database found."
    fi
fi

echo "✅ Cleanup complete!"