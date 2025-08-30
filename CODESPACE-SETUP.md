# GitHub Codespace Setup Guide

## ✅ Application Status
Your GitDM application is now **FULLY CONFIGURED** and ready to run in GitHub Codespaces!

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
./start-codespace.sh
```

### Option 2: Manual Setup
```bash
# 1. Start services
sudo -u postgres pg_ctlcluster 17 main start
sudo redis-server --daemonize yes
mkdir -p /tmp/minio-data
MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin nohup minio server /tmp/minio-data --console-address ":9001" > /tmp/minio.log 2>&1 &

# 2. Activate Python environment
source venv/bin/activate

# 3. Run migrations and start Django
python manage.py migrate --noinput
python manage.py runserver 0.0.0.0:8000
```

## 🔗 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Django App** | http://localhost:8000 | - |
| **Health Check** | http://localhost:8000/health/ | - |
| **API Documentation** | http://localhost:8000/api/docs/ | - |
| **Admin Panel** | http://localhost:8000/admin/ | admin@example.com / admin123 |
| **MinIO Console** | http://localhost:9001/ | minioadmin / minioadmin |

## 🛠️ Services Configuration

### ✅ PostgreSQL
- **Status**: Installed and configured
- **Database**: gitdm_db
- **User**: gitdm_user
- **Password**: gitdm_password
- **Host**: localhost:5432

### ✅ Redis
- **Status**: Installed and running
- **Host**: localhost:6379
- **Use**: Caching, Celery broker, session storage

### ✅ MinIO
- **Status**: Installed and running
- **Console**: http://localhost:9001/
- **API**: http://localhost:9000/
- **Credentials**: minioadmin / minioadmin
- **Buckets**: media, static

### ✅ Django Application
- **Framework**: Django 5.2.5
- **Database**: PostgreSQL (configured)
- **Authentication**: JWT with email-based users
- **API**: REST API with Swagger documentation

## 🔧 Environment Configuration

The `.env` file has been configured with:
- PostgreSQL connection settings
- Redis configuration
- MinIO storage settings
- JWT authentication
- Debug mode enabled for development

## 📦 Dependencies

All Python dependencies are installed in the virtual environment:
- Django & DRF
- PostgreSQL driver (psycopg2)
- Redis client
- MinIO/S3 storage
- Celery for background tasks
- JWT authentication
- OpenAI integration

## 🎯 Next Steps

1. **Start the application**: Run `./start-codespace.sh`
2. **Access the admin**: Go to http://localhost:8000/admin/
3. **Test the API**: Visit http://localhost:8000/api/docs/
4. **Configure MinIO buckets**: Access MinIO console at http://localhost:9001/

## 🐛 Troubleshooting

### If services don't start:
```bash
# Check PostgreSQL
sudo -u postgres pg_ctlcluster 17 main status

# Check Redis
redis-cli ping

# Check MinIO
curl http://localhost:9000/minio/health/live
```

### If Django fails:
```bash
source venv/bin/activate
python manage.py check
python manage.py migrate
```

## 🔒 Security Notes

- This setup is configured for **development only**
- Default credentials are used (change in production)
- DEBUG mode is enabled
- All hosts are allowed (ALLOWED_HOSTS=*)

Your application is ready to run in GitHub Codespaces! 🎉