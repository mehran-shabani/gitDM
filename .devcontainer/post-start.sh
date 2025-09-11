#!/bin/bash
set -e

echo "🔄 Starting development environment..."

# Run any pending migrations
echo "🔄 Checking for pending migrations..."
python manage.py migrate --noinput

echo "✨ Development environment is ready!"

# Start backend in background
echo "🚀 Starting Django backend server..."
python manage.py runserver 0.0.0.0:8000 &
BACKEND_PID=$!

# Start frontend in background
echo "🌐 Starting React frontend server..."
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000 &
FRONTEND_PID=$!
cd ..

# Store PIDs for cleanup
echo $BACKEND_PID > /tmp/backend.pid
echo $FRONTEND_PID > /tmp/frontend.pid

# Run tests to verify setup
if [ -f .devcontainer/test-setup.sh ]; then
  echo ""
  bash .devcontainer/test-setup.sh
fi

echo ""
echo "🚀 Services started successfully!"
echo "   - Django backend: http://localhost:8000"
echo "   - React frontend: http://localhost:3000"
echo "   - Admin panel: http://localhost:8000/admin"
echo "   - API docs: http://localhost:8000/api/docs/"
echo ""
echo "📝 Default credentials:"
echo "   - Django admin: admin / admin123"
echo ""
echo "🛑 To stop services:"
echo "   - Backend: kill \$(cat /tmp/backend.pid)"
echo "   - Frontend: kill \$(cat /tmp/frontend.pid)"