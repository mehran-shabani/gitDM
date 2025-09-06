# API Monitor - Health Check & AI Analysis System

A comprehensive Django-based API monitoring system that performs periodic health checks on configured APIs, logs results with rotation, provides a REST API and dashboard for viewing results, and uses AI to analyze logs and generate actionable insights.

## Features

- **Periodic Health Checks**: Automated health monitoring for multiple APIs with configurable intervals
- **Smart Retry Logic**: Exponential backoff retry mechanism for failed requests
- **Comprehensive Logging**: Structured JSON logging with automatic log rotation
- **AI-Powered Analysis**: Anomaly detection using Isolation Forest and intelligent summarization
- **REST API**: Full CRUD operations for services and read access to results/digests
- **Admin Dashboard**: Django admin interface for managing services and viewing results
- **Flexible Configuration**: Environment-based configuration with sensible defaults
- **Production Ready**: Docker support, comprehensive tests, and proper error handling

## Technology Stack

- **Backend**: Django 5.0, Django REST Framework
- **Task Queue**: Celery with Redis broker
- **HTTP Client**: httpx with timeout and retry support
- **ML/AI**: scikit-learn (Isolation Forest), OpenAI API (optional)
- **Database**: PostgreSQL/SQLite
- **Testing**: pytest, pytest-django, model-bakery

## Project Structure

```
apimonitor/
├── apimonitor/           # Django project settings
│   ├── settings.py       # Project settings with env support
│   ├── celery.py         # Celery configuration
│   └── urls.py           # Root URL configuration
├── monitor/              # Main application (replace with your <APP_NAME>)
│   ├── models.py         # Service, HealthCheckResult, AIDigest models
│   ├── health.py         # Health check implementation
│   ├── tasks.py          # Celery tasks for checks and analysis
│   ├── serializers.py    # DRF serializers
│   ├── views.py          # API viewsets and endpoints
│   ├── admin.py          # Django admin configuration
│   └── management/       # Custom management commands
├── tests/                # Comprehensive test suite
├── logs/                 # Log files with rotation
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Docker orchestration
└── README.md            # This file
```

## Quick Start

### Local Development

1. **Clone and setup environment**:
```bash
cd apimonitor
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Setup database**:
```bash
python manage.py migrate
python manage.py createsuperuser
```

4. **Seed initial services**:
```bash
python manage.py seed_services --file services.json
```

5. **Start services**:
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker
celery -A apimonitor worker -l info

# Terminal 3: Celery Beat
celery -A apimonitor beat -l info

# Terminal 4: Django
python manage.py runserver
```

### Docker Deployment

1. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your settings
```

2. **Build and run**:
```bash
docker-compose up --build
```

3. **Setup database and seed data**:
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py seed_services --file services.json
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | `true` |
| `ALLOWED_HOSTS` | Allowed hosts | `*` |
| `DATABASE_URL` | Database connection | `sqlite:///db.sqlite3` |
| `REDIS_URL` | Redis connection | `redis://localhost:6379/0` |
| `HEALTH_INTERVAL_CRON` | Health check interval | `*/5 * * * *` |
| `OPENAI_API_KEY` | OpenAI API key (optional) | Empty |
| `SERVICES_JSON` | Path to services config | `./services.json` |

### Services Configuration

Create a `services.json` file:

```json
[
  {
    "name": "UsersAPI",
    "base_url": "https://api.example.com",
    "health_path": "/health",
    "method": "GET",
    "headers": {"X-API-Key": "abc123"},
    "timeout_s": 3,
    "enabled": true
  },
  {
    "name": "Billing",
    "base_url": "https://billing.example.com",
    "health_path": "/status",
    "method": "HEAD",
    "headers": {},
    "timeout_s": 2,
    "enabled": true
  }
]
```

## API Endpoints

### Services
- `GET/POST /api/monitor/services/` - List/Create services
- `GET/PUT/PATCH/DELETE /api/monitor/services/{id}/` - Service details

### Health Check Results
- `GET /api/monitor/results/` - List results with filters:
  - `?service={id}` - Filter by service
  - `?since={iso_datetime}` - Results after timestamp
  - `?until={iso_datetime}` - Results before timestamp

### AI Digests
- `GET /api/monitor/digests/` - List all digests
- `GET /api/monitor/digests/latest/` - Latest digest
  - `?service={id}` - Latest for specific service

### Health Summary
- `GET /api/monitor/health/summary/` - Comprehensive summary including:
  - Latest check per service
  - 24-hour statistics
  - Latest AI analysis

## Features in Detail

### Health Checks
- Configurable timeout per service
- Exponential backoff retry (0.5s, 1.5s delays)
- Support for custom headers and HTTP methods
- Automatic SSL verification
- Detailed latency measurements

### Logging
- Structured JSON logging
- Automatic log rotation (5MB max, 5 backups)
- Separate health check logs
- Full error context preservation

### AI Analysis
- **Anomaly Detection**: Uses Isolation Forest to detect unusual patterns
- **Smart Summarization**: 
  - With OpenAI API: Intelligent, context-aware summaries
  - Without OpenAI: Rule-based analysis with actionable recommendations
- **Metrics Tracked**: Latency patterns, error rates, service availability

### Security
- Session-based authentication for API access
- Rate limiting (100/hour anonymous, 1000/hour authenticated)
- Secure header handling
- Environment-based secrets

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=monitor

# Run specific test file
pytest tests/test_health.py
```

## Monitoring & Maintenance

### Log Files
- `logs/health.log` - Health check results in JSONL format
- Automatic rotation at 5MB with 5 backups

### Database Indexes
- Composite index on `(service, checked_at)` for efficient queries
- Individual indexes on frequently filtered fields

### Performance Optimization
- `select_related` for reducing database queries
- Efficient time-range filtering
- Pagination for large result sets

## Troubleshooting

### Common Issues

1. **Redis Connection Error**:
   - Ensure Redis is running: `redis-cli ping`
   - Check `REDIS_URL` in `.env`

2. **No Health Checks Running**:
   - Verify Celery Beat is running
   - Check `HEALTH_INTERVAL_CRON` setting
   - Look for errors in Celery worker logs

3. **OpenAI API Errors**:
   - System works without OpenAI (uses rule-based summary)
   - Check `OPENAI_API_KEY` if using AI features

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is provided as-is for demonstration and educational purposes.