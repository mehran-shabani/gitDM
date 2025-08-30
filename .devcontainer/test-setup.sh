#!/bin/bash
set -e

echo "🧪 Testing GitHub Codespaces setup..."

# Test PostgreSQL connection
echo -n "Testing PostgreSQL... "
if PGPASSWORD=${POSTGRES_PASSWORD:-apppass} psql -h ${POSTGRES_HOST:-db} -U ${POSTGRES_USER:-appuser} -d ${POSTGRES_DB:-appdb} -c '\q' 2>/dev/null; then
    echo "✅ OK"
else
    echo "❌ Failed"
    exit 1
fi

# Test Redis connection
echo -n "Testing Redis... "
if redis-cli -h ${REDIS_HOST:-redis} ping | grep -q PONG; then
    echo "✅ OK"
else
    echo "❌ Failed"
    exit 1
fi

# Test MinIO connection
echo -n "Testing MinIO... "
if curl -f http://${MINIO_ENDPOINT:-minio:9000}/minio/health/live >/dev/null 2>&1; then
    echo "✅ OK"
else
    echo "❌ Failed"
    exit 1
fi

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
if python manage.py showmigrations | grep -q '\[X\]'; then
    echo "✅ OK"
else
    echo "❌ Failed"
    exit 1
fi

echo ""
echo "✨ All tests passed! Your GitHub Codespaces environment is ready."