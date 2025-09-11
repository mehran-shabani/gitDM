#!/usr/bin/env bash
set -euo pipefail

echo "🏥 Running health checks..."

# Function to check if a URL is accessible
check_url() {
    local url=$1
    local name=$2
    if curl -s -f "$url" >/dev/null 2>&1; then
        echo "✅ $name is accessible"
        return 0
    else
        echo "❌ $name is not accessible"
        return 1
    fi
}

# Function to check if a port is open
check_port() {
    local host=$1
    local port=$2
    local name=$3
    if nc -z "$host" "$port" 2>/dev/null; then
        echo "✅ $name ($host:$port) is accessible"
        return 0
    else
        echo "❌ $name ($host:$port) is not accessible"
        return 1
    fi
}

# Check Django backend
echo "🐍 Checking Django backend..."
if check_url "http://localhost:8000/health/" "Django Health Check"; then
    # Check additional Django endpoints
    check_url "http://localhost:8000/admin/" "Django Admin" || true
    check_url "http://localhost:8000/api/docs/" "API Documentation" || true
else
    echo "ℹ️  Django backend is not running or not accessible"
fi

# Check React frontend
echo "🌐 Checking React frontend..."
if ! check_url "http://localhost:3000" "React Frontend"; then
    echo "ℹ️  React frontend is not running or not accessible"
fi

# Check database connections
echo "🗄️ Checking database connections..."

# PostgreSQL (if running)
if check_port "localhost" "5432" "PostgreSQL"; then
    echo "ℹ️  PostgreSQL is available"
else
    echo "ℹ️  PostgreSQL is not running (SQLite might be in use)"
fi

# Redis (if running)
if check_port "localhost" "6379" "Redis"; then
    echo "ℹ️  Redis is available"
else
    echo "ℹ️  Redis is not running"
fi

# Check Docker containers (if any)
echo "🐳 Checking Docker containers..."
if command -v docker >/dev/null 2>&1; then
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(gitdm|django)" >/dev/null 2>&1; then
        echo "📊 Running Docker containers:"
        docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(gitdm|django)" || true
    else
        echo "ℹ️  No GitDM Docker containers are running"
    fi
else
    echo "ℹ️  Docker is not available"
fi

# Check Python environment
echo "🐍 Checking Python environment..."
if python --version >/dev/null 2>&1; then
    echo "✅ Python: $(python --version)"
    
    # Check if Django is importable
    if python -c "import django; print(f'Django {django.get_version()}')" 2>/dev/null; then
        echo "✅ Django is available"
    else
        echo "❌ Django is not available"
    fi
else
    echo "❌ Python is not available"
fi

# Check Node.js environment
echo "🌐 Checking Node.js environment..."
if command -v node >/dev/null 2>&1; then
    echo "✅ Node.js: $(node --version)"
    echo "✅ npm: $(npm --version)"
else
    echo "❌ Node.js is not available"
fi

echo ""
echo "🏥 Health check complete!"
echo ""
echo "💡 Tips:"
echo "  - If services are not running, try: ./scripts/start-dev.sh"
echo "  - For Docker setup, try: ./scripts/start-simple.sh"
echo "  - Check logs with: docker compose logs -f"