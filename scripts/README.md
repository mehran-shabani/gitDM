# Scripts Documentation

This directory contains utility scripts for setting up, running, and managing the GitDM project in various environments.

## Overview

The scripts are organized by environment and complexity:

- **Development Scripts**: For local development with virtual environments
- **Docker Scripts**: For containerized development and deployment
- **Utility Scripts**: For testing, setup, and maintenance

## Quick Start

### For New Users (Recommended)

```bash
# Option 1: Local development setup
./scripts/setup-dev.sh
./scripts/start-dev.sh

# Option 2: Simple Docker setup (SQLite)
./scripts/start-simple.sh

# Option 3: Full Docker setup (PostgreSQL + Redis)
./scripts/start-advanced.sh
```

## Script Reference

### Development Scripts

#### `setup-dev.sh`
Sets up the complete development environment locally.

**What it does:**
- Creates Python virtual environment
- Installs all dependencies (backend + frontend)
- Runs database migrations
- Creates admin user
- Builds frontend

**Usage:**
```bash
./scripts/setup-dev.sh
```

**Requirements:**
- Python 3.13+
- Node.js 20+
- npm

#### `start-dev.sh`
Starts both frontend and backend development servers simultaneously.

**What it does:**
- Starts Django development server on port 8000
- Starts React development server on port 3000
- Runs both in background with proper cleanup on exit

**Usage:**
```bash
./scripts/start-dev.sh
# Press Ctrl+C to stop both servers
```

#### `start-backend.sh`
Starts only the Django backend server.

**Usage:**
```bash
./scripts/start-backend.sh
```

**Serves:**
- Backend API: http://localhost:8000
- Admin panel: http://localhost:8000/admin

#### `start-frontend.sh`
Starts only the React frontend development server.

**Usage:**
```bash
./scripts/start-frontend.sh
```

**Serves:**
- Frontend: http://localhost:3000

### Docker Scripts

#### `start-simple.sh`
Starts a simple Docker setup with SQLite database.

**What it does:**
- Uses `docker-compose.simple.yml`
- SQLite database (no external dependencies)
- Single Django container
- Automatic migrations and superuser creation

**Usage:**
```bash
./scripts/start-simple.sh
```

**Services:**
- Django: http://localhost:8000

**Stop with:**
```bash
./scripts/stop-simple.sh
```

#### `start-advanced.sh`
Starts full Docker setup with all services.

**What it does:**
- Uses `docker-compose.full.yml`
- PostgreSQL database
- Redis for Celery
- Frontend and backend containers
- Celery workers for background tasks

**Usage:**
```bash
./scripts/start-advanced.sh
```

**Services:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

**Stop with:**
```bash
./scripts/stop-advanced.sh
```

#### `stop-simple.sh` / `stop-advanced.sh`
Stops and cleans up Docker containers, networks, and volumes.

### Utility Scripts

#### `test.sh`
Runs the complete test suite for both frontend and backend.

**What it does:**
- Runs pytest for backend tests
- Runs ESLint for frontend linting
- Builds frontend to check for errors
- Can be extended for additional test types

**Usage:**
```bash
./scripts/test.sh
```

## Environment-Specific Usage

### Local Development

Best for:
- Active development and debugging
- IDE integration
- Fast iteration cycles

```bash
./scripts/setup-dev.sh    # One-time setup
./scripts/start-dev.sh     # Start development
```

### GitHub Codespaces

The devcontainer automatically runs setup. Just start the services:

```bash
# Backend only (automatic in Codespaces)
python manage.py runserver 0.0.0.0:8000

# Frontend (manual)
cd frontend && npm run dev

# Or both
./scripts/start-dev.sh
```

### Docker Development

Best for:
- Consistent environment across team
- Production-like setup
- Testing deployment configurations

```bash
# Simple setup (quick start)
./scripts/start-simple.sh

# Full setup (production-like)
./scripts/start-advanced.sh
```

## Troubleshooting

### Common Issues

1. **Permission denied**
   ```bash
   chmod +x scripts/*.sh
   ```

2. **Port already in use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   # Kill the process or use different port
   ```

3. **Docker issues**
   ```bash
   # Clean up Docker
   docker system prune -f
   docker volume prune -f
   ```

4. **Database issues**
   ```bash
   # Reset database (WARNING: loses data)
   rm db.sqlite3
   python manage.py migrate
   ```

### Environment Variables

All scripts respect the `.env` file. Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
# Edit .env with your settings
```

### Script Dependencies

| Script | Python | Node.js | Docker | Database |
|--------|--------|---------|--------|----------|
| `setup-dev.sh` | ✅ | ✅ | ❌ | SQLite |
| `start-dev.sh` | ✅ | ✅ | ❌ | SQLite |
| `start-simple.sh` | ❌ | ❌ | ✅ | SQLite |
| `start-advanced.sh` | ❌ | ❌ | ✅ | PostgreSQL |

## Contributing

When adding new scripts:

1. Follow the existing naming convention
2. Include proper error handling (`set -euo pipefail`)
3. Add helpful output messages with emojis
4. Update this README
5. Make scripts executable (`chmod +x`)
6. Test in multiple environments

## Support

For issues with these scripts:

1. Check the troubleshooting section above
2. Verify your environment meets the requirements
3. Check the GitHub issues for known problems
4. Create a new issue with environment details