#!/bin/bash
set -e

echo "🧪 Testing GitHub Codespaces setup..."

# Test Django
echo -n "Testing Django... "
if python manage.py check >/dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ Failed"
    exit 1
fi

# Test migrations
echo -n "Testing migrations... "
if python manage.py migrate --check --noinput >/dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ Failed"
    exit 1
fi

# Test database (SQLite)
echo -n "Testing database... "
if python -c "from django.db import connection; connection.ensure_connection()" 2>/dev/null; then
    echo "✅ OK"
else
    echo "❌ Failed"
    exit 1
fi

# Test superuser exists
echo -n "Testing superuser... "
if python -c "import sys; from django.contrib.auth import get_user_model; User = get_user_model(); sys.exit(0 if User.objects.filter(username='admin').exists() else 1)" 2>/dev/null; then
    echo "✅ OK"
else
    echo "❌ Failed"
    exit 1
fi

echo ""
echo "✨ All tests passed! Your GitHub Codespaces environment is ready."