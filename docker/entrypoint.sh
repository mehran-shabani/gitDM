#!/bin/bash

# exit on error
set -o errexit

# Apply migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static
echo "Collecting static files..."
python manage.py collectstatic --noinput

exec "$@"
