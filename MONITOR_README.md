# API Health Monitoring System

یک سیستم جامع برای نظارت بر سلامت APIها با قابلیت‌های زیر:
- چک سلامت دوره‌ای APIها
- ثبت کامل نتایج در دیتابیس و فایل‌های لاگ
- تحلیل هوشمند لاگ‌ها با AI
- داشبورد REST API برای مشاهده نتایج

## ویژگی‌ها

### 🔍 Health Monitoring
- چک خودکار سلامت APIها هر 5 دقیقه
- پشتیبانی از HTTP methods مختلف (GET, POST, HEAD)
- Retry logic با exponential backoff
- اندازه‌گیری دقیق latency
- ثبت کامل خطاها و متادیتا

### 📊 Logging & Analytics
- ثبت نتایج در دیتابیس با ایندکس‌های بهینه
- فایل‌های لاگ JSONL با rotation خودکار
- تحلیل anomaly detection با scikit-learn
- خلاصه‌سازی هوشمند با OpenAI (اختیاری)

### 🚀 REST API
- CRUD کامل برای مدیریت سرویس‌ها
- فیلتر و جستجوی پیشرفته نتایج
- endpoint خلاصه سلامت تمام سرویس‌ها
- Authentication و throttling

### 🤖 AI Analysis
- تشخیص خودکار anomaly در latency و error rate
- خلاصه‌سازی متنی با پیشنهادات عملی
- تحلیل global و per-service
- پشتیبانی از OpenAI و fallback محلی

## نصب و راه‌اندازی

### پیش‌نیازها
- Python 3.11+
- Redis Server
- (اختیاری) Docker & Docker Compose

### روش 1: نصب محلی

#### 1. آماده‌سازی محیط
```bash
# ایجاد virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# یا
.venv\Scripts\activate  # Windows

# نصب وابستگی‌ها
pip install -r requirements.txt
```

#### 2. تنظیم متغیرهای محیطی
```bash
# کپی و ویرایش فایل محیطی
cp .env.example .env

# ویرایش .env با تنظیمات مناسب:
# - DJANGO_SECRET_KEY: کلید امنیتی Django
# - REDIS_URL: آدرس Redis server
# - OPENAI_API_KEY: کلید OpenAI (اختیاری)
```

#### 3. راه‌اندازی دیتابیس
```bash
# اجرای migrations
python manage.py migrate

# ایجاد superuser
python manage.py createsuperuser

# بارگذاری سرویس‌های نمونه
python manage.py seed_services --file services.json
```

#### 4. اجرای سرویس‌ها
```bash
# Terminal 1: Redis Server
redis-server

# Terminal 2: Django Development Server
python manage.py runserver

# Terminal 3: Celery Worker
celery -A config worker -l info

# Terminal 4: Celery Beat Scheduler
celery -A config beat -l info
```

### روش 2: Docker Compose

```bash
# ساخت و اجرای تمام سرویس‌ها
docker-compose up --build

# یا در background
docker-compose up -d --build

# مشاهده logs
docker-compose logs -f

# توقف سرویس‌ها
docker-compose down
```

## استفاده از API

### Authentication
همه endpointها نیاز به authentication دارند. از JWT token استفاده کنید:

```bash
# دریافت token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# استفاده از token
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/monitor/services/
```

### API Endpoints

#### Services Management
```bash
# لیست سرویس‌ها
GET /api/monitor/services/

# ایجاد سرویس جدید
POST /api/monitor/services/
{
  "name": "MyAPI",
  "base_url": "https://my-api.com",
  "health_path": "/health",
  "method": "GET",
  "headers": {"X-API-Key": "secret"},
  "timeout_s": 5,
  "enabled": true
}

# ویرایش سرویس
PATCH /api/monitor/services/{id}/

# حذف سرویس
DELETE /api/monitor/services/{id}/
```

#### Health Check Results
```bash
# لیست نتایج (با فیلتر)
GET /api/monitor/results/?service=1&since=2024-01-01T00:00:00Z&until=2024-01-02T00:00:00Z

# جزئیات یک نتیجه
GET /api/monitor/results/{id}/
```

#### AI Digests
```bash
# لیست تحلیل‌های AI
GET /api/monitor/digests/

# آخرین تحلیل (کل سیستم یا یک سرویس)
GET /api/monitor/digests/latest/
GET /api/monitor/digests/latest/?service=1
```

#### Health Summary
```bash
# خلاصه کامل سلامت سیستم
GET /api/monitor/health/summary/
```

نمونه پاسخ:
```json
{
  "services": [
    {
      "service_id": 1,
      "service_name": "UsersAPI",
      "latest_check": {
        "status_code": 200,
        "ok": true,
        "latency_ms": 145,
        "checked_at": "2024-01-15T10:30:00Z"
      },
      "latest_digest": {
        "summary_text": "Service performing well...",
        "anomaly_count": 2,
        "period_start": "2024-01-14T10:00:00Z"
      }
    }
  ],
  "global_digest": {
    "summary_text": "Overall system health is good...",
    "anomaly_count": 5
  },
  "generated_at": "2024-01-15T10:31:00Z"
}
```

## مدیریت از طریق Django Admin

Admin panel در آدرس `http://localhost:8000/admin/` قابل دسترس است:

- **Services**: مدیریت کامل سرویس‌ها با رابط گرافیکی
- **Health Check Results**: مشاهده تاریخچه نتایج با فیلتر و جستجو
- **AI Digests**: مشاهده تحلیل‌های AI با preview خلاصه

## تنظیمات پیشرفته

### متغیرهای محیطی

| متغیر | پیش‌فرض | توضیح |
|-------|---------|--------|
| `HEALTH_INTERVAL_CRON` | `*/5 * * * *` | زمان‌بندی health check (cron format) |
| `REDIS_URL` | `redis://localhost:6379/0` | آدرس Redis server |
| `OPENAI_API_KEY` | - | کلید OpenAI برای تحلیل هوشمند |
| `SERVICES_JSON` | `./services.json` | مسیر فایل سرویس‌های اولیه |

### Celery Tasks

#### Health Check Task
```python
# اجرای دستی
from monitor.tasks import run_health_checks
result = run_health_checks.delay()
```

#### AI Analysis Task
```python
# تحلیل 24 ساعت گذشته
from monitor.tasks import analyze_logs
result = analyze_logs.delay(period_hours=24)
```

### Logging Configuration

لاگ‌ها در دایرکتوری `logs/` ذخیره می‌شوند:
- `health.log`: نتایج health check (JSONL format با rotation)
- `monitor.log`: لاگ‌های عمومی اپلیکیشن

## نمونه فایل services.json

```json
[
  {
    "name": "UsersAPI",
    "base_url": "https://api.example.com",
    "health_path": "/health",
    "method": "GET",
    "headers": {"X-API-Key": "abc"},
    "timeout_s": 3,
    "enabled": true
  },
  {
    "name": "PaymentGateway",
    "base_url": "https://payments.example.com",
    "health_path": "/status",
    "method": "HEAD",
    "headers": {},
    "timeout_s": 5,
    "enabled": true
  }
]
```

## اجرای تست‌ها

```bash
# اجرای تمام تست‌ها
pytest

# اجرای تست‌های مربوط به monitor app
pytest monitor/tests/

# اجرای تست‌ها با coverage
pytest --cov=monitor

# اجرای تست خاص
pytest monitor/tests/test_models.py::TestServiceModel::test_service_creation
```

## نظارت و عیب‌یابی

### Health Check Logs
```bash
# مشاهده لاگ‌های health check
tail -f logs/health.log

# فیلتر نتایج ناموفق
grep '"ok": false' logs/health.log
```

### Celery Monitoring
```bash
# وضعیت worker
celery -A config inspect active

# وضعیت scheduled tasks
celery -A config inspect scheduled

# آمار worker
celery -A config inspect stats
```

### Database Queries
```python
# آخرین نتایج هر سرویس
from monitor.models import Service, HealthCheckResult
from django.db.models import Max

services_status = Service.objects.annotate(
    latest_check=Max('health_results__checked_at')
).values('name', 'latest_check')

# سرویس‌های با بیشترین خطا در 24 ساعت گذشته
from django.utils import timezone
yesterday = timezone.now() - timezone.timedelta(days=1)

error_stats = HealthCheckResult.objects.filter(
    checked_at__gte=yesterday,
    ok=False
).values('service__name').annotate(
    error_count=models.Count('id')
).order_by('-error_count')
```

## عملکرد و بهینه‌سازی

### Database Optimization
- ایندکس‌های composite روی `(service, checked_at)`
- استفاده از `select_related` برای کاهش query count
- Pagination برای endpoint های لیست

### Celery Optimization
- Worker concurrency قابل تنظیم
- Task routing برای تفکیک health check و AI analysis
- Graceful shutdown handling

### Memory Management
- Log rotation برای جلوگیری از پر شدن disk
- Cleanup قدیمی‌ترین رکوردها (اختیاری)

## توسعه و سفارشی‌سازی

### اضافه کردن Health Check جدید
1. سرویس جدید در `services.json` تعریف کنید
2. `python manage.py seed_services --file services.json --update` اجرا کنید

### سفارشی‌سازی AI Analysis
در `monitor/tasks.py`:
- `_detect_anomalies()`: تنظیم پارامترهای IsolationForest
- `_generate_summary()`: شخصی‌سازی rule-based summary
- OpenAI prompts: ویرایش prompt برای بهتر شدن نتایج

### اضافه کردن Alerting
```python
# در monitor/tasks.py
def send_alert(service, result):
    if not result['ok']:
        # ارسال alert (email, Slack, etc.)
        pass
```

## مشکلات رایج

### Redis Connection Error
```bash
# بررسی وضعیت Redis
redis-cli ping

# راه‌اندازی Redis
redis-server
# یا
sudo systemctl start redis
```

### Celery Worker Not Starting
```bash
# بررسی Redis connectivity
celery -A config inspect ping

# اجرای worker با debug
celery -A config worker -l debug
```

### Migration Errors
```bash
# Reset migrations (development only)
python manage.py migrate monitor zero
python manage.py makemigrations monitor
python manage.py migrate
```

## مجوز و نگهداری

این پروژه برای نظارت بر سلامت APIها در محیط‌های production طراحی شده است.

برای سوالات و پشتیبانی، لطفاً issue ایجاد کنید.

---

**نکات امنیتی:**
- در production حتماً `DJANGO_SECRET_KEY` و `OPENAI_API_KEY` را تنظیم کنید
- از HTTPS برای تمام ارتباطات استفاده کنید
- Redis را با authentication راه‌اندازی کنید
- Log files را از دسترسی عمومی محافظت کنید