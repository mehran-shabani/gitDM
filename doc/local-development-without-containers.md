# Running Django Application Without Containers

**IMPORTANT**: This guide explains how to run the Django application locally without using Docker containers for MinIO, PostgreSQL, and Redis. This approach is suitable for development environments where you want to use local installations of these services.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Service Installation](#service-installation)
  - [PostgreSQL](#postgresql)
  - [Redis](#redis)
  - [MinIO](#minio)
- [Application Configuration](#application-configuration)
- [Running the Application](#running-the-application)
- [Alternative: Using SQLite and File Storage](#alternative-using-sqlite-and-file-storage)

## Prerequisites

- Python 3.11 or higher
- pip or pipx for package management
- Access to install system packages (for PostgreSQL, Redis)

## Service Installation

### PostgreSQL

#### Ubuntu/Debian:
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
```

In the PostgreSQL prompt:
```sql
CREATE DATABASE diabetes;
CREATE USER diabetes WITH PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE diabetes TO diabetes;
\q
```

#### macOS:
```bash
# Using Homebrew
brew install postgresql
brew services start postgresql

# Create database and user
psql postgres
```

Then run the same SQL commands as above.

#### Windows:
Download and install PostgreSQL from [https://www.postgresql.org/download/windows/](https://www.postgresql.org/download/windows/)

### Redis

#### Ubuntu/Debian:
```bash
# Install Redis
sudo apt update
sudo apt install redis-server

# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Test Redis
redis-cli ping
```

#### macOS:
```bash
# Using Homebrew
brew install redis
brew services start redis

# Test Redis
redis-cli ping
```

#### Windows:
Download Redis from [https://github.com/microsoftarchive/redis/releases](https://github.com/microsoftarchive/redis/releases) or use WSL2.

### MinIO

#### All Platforms:

1. Download MinIO binary from [https://min.io/download](https://min.io/download)

2. Run MinIO:
```bash
# Linux/macOS
chmod +x minio
./minio server ~/minio-data --console-address ":9001"

# Windows
minio.exe server C:\minio-data --console-address ":9001"
```

3. Note the credentials displayed in the console (or set custom ones):
   - Default Access Key: minioadmin
   - Default Secret Key: minioadmin
   - API: http://localhost:9000
   - Console: http://localhost:9001

4. Create buckets using MinIO Console (http://localhost:9001):
   - Login with the credentials
   - Create bucket named `media`
   - Create bucket named `static`

## Application Configuration

1. **Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. **Create `.env` file:**
```bash
cp .env.example .env
```

4. **Configure `.env` file:**
```env
# Django settings
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=your-very-secure-secret-key-here

# PostgreSQL settings (local)
POSTGRES_DB=diabetes
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=your-secure-password
POSTGRES_PORT=5432
POSTGRES_USER=diabetes

# Redis settings (local)
REDIS_URL=redis://localhost:6379/0

# MinIO settings (local)
MINIO_STORAGE_ACCESS_KEY=minioadmin
MINIO_STORAGE_ENDPOINT=localhost:9000
MINIO_STORAGE_MEDIA_BUCKET=media
MINIO_STORAGE_SECRET_KEY=minioadmin
MINIO_STORAGE_STATIC_BUCKET=static
MINIO_STORAGE_USE_HTTPS=False
```

5. **Run database migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Create a superuser:**
```bash
python manage.py createsuperuser
```

7. **Collect static files:**
```bash
python manage.py collectstatic --noinput
```

## Running the Application

### Start all services:

1. **Ensure PostgreSQL is running:**
```bash
# Check status
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS
```

2. **Ensure Redis is running:**
```bash
# Check status
sudo systemctl status redis-server  # Linux
brew services list | grep redis  # macOS
redis-cli ping  # Should return PONG
```

3. **Start MinIO:**
```bash
# In a separate terminal
./minio server ~/minio-data --console-address ":9001"
```

4. **Run Django development server:**
```bash
python manage.py runserver
```

5. **Run Celery worker (in a separate terminal):**
```bash
celery -A config worker -l info
```

6. **Run Celery beat (in another separate terminal):**
```bash
celery -A config beat -l info
```

### Access the application:
- Django Admin: http://localhost:8000/admin/
- API Documentation: http://localhost:8000/api/schema/swagger-ui/
- MinIO Console: http://localhost:9001/

## Alternative: Using SQLite and File Storage

If you want to run the application without any external services, you can create a local settings file:

1. **Create `config/local_settings.py`:**
```python
from .settings import *

# Use SQLite
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Use local file storage instead of MinIO
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Use local memory cache instead of Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Disable Celery for local development
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
```

2. **Use local settings:**
```bash
export DJANGO_SETTINGS_MODULE=config.local_settings
python manage.py migrate
python manage.py runserver
```

## Troubleshooting

### PostgreSQL Connection Issues:
- Check if PostgreSQL is running: `pg_isready`
- Verify credentials: `psql -U diabetes -d diabetes -h localhost`
- Check PostgreSQL logs: `sudo journalctl -u postgresql`

### Redis Connection Issues:
- Test connection: `redis-cli ping`
- Check if Redis is listening: `netstat -an | grep 6379`
- Check Redis logs: `sudo journalctl -u redis-server`

### MinIO Issues:
- Ensure buckets are created
- Check if MinIO is accessible: `curl http://localhost:9000/minio/health/live`
- Verify credentials are correct in `.env`

### Django Issues:
- Check for migration issues: `python manage.py showmigrations`
- Verify environment variables: `python manage.py shell -c "from django.conf import settings; print(settings.DATABASES)"`
- Check Django logs for detailed error messages

## Notes

- This setup is for development purposes only
- For production, use proper service management and security configurations
- Always use strong passwords and keep them secure
- Consider using environment-specific settings files for different environments