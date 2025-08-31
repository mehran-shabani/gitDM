# GitHub Codespaces Setup - Simplified Django Configuration

This document describes the simplified configuration for running the project in GitHub Codespaces with Django defaults (SQLite, local static/media). External services like PostgreSQL, Redis, and MinIO are not used in this mode.

## Changes Made

### 1. Settings Configuration (`config/settings.py`)
- **Database**: Now uses SQLite only (removed PostgreSQL configuration)
- **Cache**: Uses Django's default `LocMemCache` (removed Redis)
- **File Storage**: Uses Django's default file storage (removed MinIO)
- **Celery**: Configuration commented out (no message broker available)
- **Added GitHub Codespaces specific settings** for ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS

### 2. Dependencies (`requirements.txt`)
The dependency set keeps Django, DRF, JWT, and Spectacular. Celery libraries are present for future use but are inactive without a broker in Codespaces.

### 3. Docker Configuration
- **docker-compose.yml**: Single `web` service (SQLite + Django)
- **Dockerfile**: Python base with app dependencies
- **bootstrap.sh**: Starts `web`, applies migrations, creates admin, collects static

### 4. Development Container (`.devcontainer/`)
- **devcontainer.json**: Removed port forwarding for PostgreSQL, Redis, and MinIO
- **post-create.sh**: Removed service health checks
- **post-start.sh**: Simplified to only check Django
- **test-setup.sh**: Updated to test SQLite and Django only

### 5. GitHub Actions (`.github/workflows/`)
- **codespaces-test.yml**: Removed PostgreSQL and Redis service containers

### 6. Environment Variables (`.env.example`)
An example file is provided at project root. Copy to `.env` if needed:

```bash
cp .env.example .env
```

Contains placeholders for Django settings and optional external services (PostgreSQL/Redis/MinIO) for non-Codespaces deployments.

## Usage in GitHub Codespaces

1. Open the repository in GitHub Codespaces
2. The environment will automatically set up using SQLite
3. Migrations will run automatically
4. A superuser is created (username: `admin`, password: `admin123`)
5. The Django development server will be available at the forwarded port
   - In Codespaces: `https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}`
   - Local: `http://localhost:8000`
## Notes

- All data is stored in SQLite (`db.sqlite3`)
- Static and media files are stored locally in the filesystem
- Celery tasks do not run without a message broker
- This setup is optimized for development in GitHub Codespaces