#!/bin/bash
set -e

echo "🔄 Starting development environment..."

# Run any pending migrations
echo "🔄 Checking for pending migrations..."
python manage.py migrate --noinput

echo "✨ Development environment is ready!"

# Run tests to verify setup
if [ -f .devcontainer/test-setup.sh ]; then
  echo ""
  bash .devcontainer/test-setup.sh
fi

echo ""
echo "🚀 Quick start guide:"
echo "   - Django app: http://localhost:8000"
echo "   - Admin panel: http://localhost:8000/admin"
echo "   - API docs: http://localhost:8000/api/docs/"
echo ""
echo "📝 Default credentials:"
echo "   - Django admin: admin / admin123"