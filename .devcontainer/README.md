# GitHub Codespaces Setup

This directory contains the configuration for running this Django application in GitHub Codespaces.

## 🚀 Quick Start

1. Open this repository in GitHub Codespaces
2. Wait for the environment to be set up (this happens automatically)
3. The application will be available at the forwarded port URL

## 📦 What's Included

- **PostgreSQL 15**: Database server
- **Redis 7**: Cache and message broker
- **MinIO**: S3-compatible object storage
- **Celery**: Background task processing
- **Celery Beat**: Scheduled tasks

## 🔐 Default Credentials

### Django Admin
- **URL**: `/admin`
- **Username**: `admin`
- **Password**: `admin123`

### MinIO Console
- **URL**: Port 9001
- **Username**: `minioadmin`
- **Password**: `minioadmin`

### PostgreSQL
- **Database**: `appdb`
- **Username**: `appuser`
- **Password**: `apppass`

## 📁 File Structure

```
.devcontainer/
├── devcontainer.json    # Main configuration file
├── post-create.sh       # Script that runs after container creation
├── post-start.sh        # Script that runs on container start
└── README.md           # This file
```

## 🛠️ Configuration

The setup automatically:

1. Creates a `.env` file from `.env.example`
2. Installs all Python dependencies
3. Sets up and configures all services
4. Runs database migrations
5. Creates a superuser account
6. Collects static files

## 🔧 Customization

To customize the setup:

1. Edit `.env.example` for default environment variables
2. Modify `devcontainer.json` for VS Code extensions and settings
3. Update `docker-compose.yml` for service configurations
4. Adjust scripts in `.devcontainer/` for custom setup steps

## 📝 Environment Variables

Key environment variables that are automatically configured:

- `ALLOWED_HOSTS`: Automatically includes Codespaces URLs
- `POSTGRES_HOST`: Set to `db` (Docker service name)
- `REDIS_HOST`: Set to `redis` (Docker service name)
- `MINIO_ENDPOINT`: Set to `minio:9000`

## 🐛 Troubleshooting

If you encounter issues:

1. Check the logs: `docker compose logs`
2. Restart services: `docker compose restart`
3. Rebuild containers: `docker compose down && docker compose up -d --build`
4. Check service health: `docker compose ps`

## 📚 Additional Resources

- [Django Documentation](https://docs.djangoproject.com/)
- [GitHub Codespaces Documentation](https://docs.github.com/en/codespaces)
- [MinIO Documentation](https://docs.min.io/)