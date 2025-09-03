# GitDM – سامانه مدیریت دیابت (Django + DRF)

GitDM یک سامانهٔ مدیریت و نسخه‌بندی داده‌های بیماران دیابتی است که بر پایهٔ Django 5 و Django REST Framework ساخته شده و دارای مستندسازی OpenAPI، احراز هویت JWT و زیرسامانه‌های مواجهه بالینی، آزمایشگاه، نسخه‌های دارویی، مراجع بالینی و خلاصه‌سازی هوش‌مصنوعی است.

این سند مرجع واحد مخزن است و تمام امکانات، راه‌اندازی و APIها را پوشش می‌دهد.

## 🚀 شروع سریع

- اجرا با Docker (توصیه‌شده برای توسعه):
  1) فایل محیطی را در صورت نیاز ایجاد کنید: `cp .env.example .env` (در صورت موجود بودن)
  2) اسکریپت بوت‌استرپ: `./bootstrap.sh`
  3) برنامه در `http://localhost:8000` در دسترس است
  4) اطلاعات پیش‌فرض محیط توسعه:
     - Django Admin: کاربر `admin` با گذرواژهٔ `admin123` (در صورت نبود، به‌صورت خودکار ساخته می‌شود)

- اجرا روی GitHub Codespaces:
  - پس از باز شدن Codespace، راه‌اندازی خودکار انجام می‌شود (SQLite، مهاجرت‌ها، جمع‌آوری فایل‌های استاتیک). آدرس از طریق پورت فوروارد شدهٔ 8000 در دسترس است.

- اجرای محلی بدون Docker:
  1) ساخت و فعال‌سازی محیط مجازی: `python -m venv .venv && source .venv/bin/activate`
  2) نصب وابستگی‌ها: `pip install -r requirements.txt`
  3) ایجاد فایل `.env` (در صورت نیاز)
  4) مهاجرت دیتابیس: `python manage.py migrate`
  5) اجرا: `python manage.py runserver`

### متغیرهای محیطی نمونه

فایل نمونهٔ زیر برای محیط‌های خارج از Codespaces پیشنهاد می‌شود:

```python
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# پایگاه‌داده بیرونی (اختیاری)
POSTGRES_DB=diabetes
POSTGRES_USER=diabetes
POSTGRES_PASSWORD=your-postgres-password
POSTGRES_HOST=your-postgres-host
POSTGRES_PORT=5432

# Redis (اختیاری)
REDIS_URL=redis://your-redis-host:6379/0

# MinIO (اختیاری)
MINIO_ENDPOINT=your-minio-host:9000
MINIO_ACCESS_KEY=your-minio-access-key
MINIO_SECRET_KEY=your-minio-secret-key
MINIO_USE_HTTPS=False
MINIO_MEDIA_BUCKET=media
MINIO_STATIC_BUCKET=static
```

در حالت Codespaces، به‌صورت پیش‌فرض از SQLite و فایل‌سیستم محلی استفاده می‌شود و Celery غیرفعال است.

## 📚 مستندات API و نقاط دسترسی

- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema (JSON): `/api/schema/`
- Health Check: `/health/`
- ریشهٔ API: `/api/` (وضعیت را برمی‌گرداند)

### احراز هویت (JWT)

- دریافت توکن دسترسی/نوسازی: `POST /api/token/`
- نوسازی توکن: `POST /api/token/refresh/`

نمونه درخواست دریافت توکن:

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H 'Content-Type: application/json' \
  -d '{"email": "user@example.com", "password": "pass"}'
```

درخواست‌های محافظت‌شده باید هدر زیر را داشته باشند:

```bash
Authorization: Bearer <ACCESS_TOKEN>
```

یادداشت: در ماژول مسیرها برای سازگاری، مسیرهای جایگزین دیگری هم وجود دارند؛ ولی مسیرهای بالا مرجع اصلی‌اند.

### منابع اصلی (ViewSetها)

پیشوند همهٔ مسیرهای زیر `/api/` است.

- بیماران (`patients`): CRUD و تایم‌لاین
  - `GET /patients/` فهرست بیماران (محدود به دسترسی کاربر)
  - `POST /patients/` ایجاد بیمار جدید (پزشک فعلی به‌عنوان `primary_doctor` ثبت می‌شود)
  - `GET /patients/{id}/` مشاهدهٔ جزئیات
  - `PUT/PATCH /patients/{id}/` به‌روزرسانی
  - `DELETE /patients/{id}/` حذف
  - اکشن‌ها:
    - `GET /patients/{id}/timeline/` بازگرداندن تایم‌لاین تجمیع‌شدهٔ بیمار
      - پارامتر اختیاری: `?limit=100` (حداکثر 500)

- مواجهه‌ها (`encounters`): CRUD
  - `GET /encounters/`
  - `POST /encounters/` (فیلد `created_by` خودکار از کاربر جاری تنظیم می‌شود)
  - `GET /encounters/{id}/`
  - `PUT/PATCH /encounters/{id}/`
  - `DELETE /encounters/{id}/`

- نتایج آزمایشگاه (`labs`): CRUD
  - `GET /labs/`
  - `POST /labs/`
  - `GET /labs/{id}/`
  - `PUT/PATCH /labs/{id}/`
  - `DELETE /labs/{id}/`

- دستورات دارویی (`meds`): CRUD
  - `GET /meds/`
  - `POST /meds/`
  - `GET /meds/{id}/`
  - `PUT/PATCH /meds/{id}/`
  - `DELETE /meds/{id}/`

- منابع مرجع بالینی (`refs`): CRUD
  - `GET /refs/`
  - `POST /refs/`
  - `GET /refs/{id}/`
  - `PUT/PATCH /refs/{id}/`
  - `DELETE /refs/{id}/`

- خلاصه‌های هوش‌مصنوعی (`ai-summaries`)
  - `GET /ai-summaries/` فهرست (با امکان فیلتر `?patient_id=<uuid>`)
  - `POST /ai-summaries/` ایجاد (طبق تنظیمات OpenAI/GapGPT؛ ممکن است همزمان/ناهمزمان برگردد)
  - `GET /ai-summaries/{id}/` مشاهدهٔ خلاصه
  - `DELETE /ai-summaries/{id}/` حذف
  - اکشن‌ها:
    - `POST /ai-summaries/{id}/regenerate/` بازتولید خلاصه (ناهمزمان)
    - `POST /ai-summaries/test/` تست اتصال سرویس AI
    - `GET /ai-summaries/stats/` آمار کلی خلاصه‌ها
    - `POST /ai-summaries/test-references/` تست لینک‌سازی مراجع بالینی

- تشخیص الگوهای غیرطبیعی (`pattern-analyses`, `anomaly-detections`, `pattern-alerts`, `baseline-metrics`)
  - `GET /pattern-analyses/` فهرست تحلیل‌های الگو
  - `POST /pattern-analyses/analyze/` درخواست تحلیل جدید
  - `GET /anomaly-detections/` فهرست ناهنجاری‌های تشخیص داده شده
  - `POST /anomaly-detections/{id}/acknowledge/` تایید ناهنجاری
  - `GET /pattern-alerts/` فهرست هشدارهای الگویی
  - `POST /pattern-alerts/{id}/resolve/` حل هشدار
  - `GET /baseline-metrics/` معیارهای پایه بیماران
  - `POST /baseline-metrics/calculate/` محاسبه معیارهای پایه

- نسخه‌بندی تغییرات (`versions`)
  - `GET /versions/{resource_type}/{resource_id}/` فهرست نسخه‌ها (خروجی: آرایه‌ای از نسخه‌ها)
  - `POST /versions/{resource_type}/{resource_id}/revert/` بازگردانی به نسخهٔ مشخص
    - بدنه: `{ "target_version": <int> }`

- خروجی‌گرفتن دادهٔ بیمار (Export)
  - `GET /export/patient/{id}/` بازگشت ساختار پایه شامل بیمار و آرایه‌های encounters/labs/medications/ai_summaries

### نمونهٔ گردش احراز هویت و ایجاد بیمار

```bash
# ایجاد کاربر و دریافت توکن (مثال)
curl -X POST http://localhost:8000/api/token/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"u1@test.com","password":"p1"}'

# استفاده از توکن برای ایجاد بیمار
curl -X POST http://localhost:8000/api/patients/ \
  -H 'Authorization: Bearer <TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"full_name":"Ali Test"}'

# مشاهدهٔ تایم‌لاین
curl -H 'Authorization: Bearer <TOKEN>' \
  http://localhost:8000/api/patients/<PID>/timeline/
```

## ⚙️ راه‌اندازی و اجرا

- Docker Compose: یک سرویس `web` اجرا می‌شود که مسئول مهاجرت دیتابیس، جمع‌آوری فایل‌های استاتیک و اجرای سرور توسعه است. اسکریپت `bootstrap.sh` این مراحل را خودکار انجام می‌دهد و در صورت نبود، ادمین پیش‌فرض می‌سازد.

- تنظیمات مهم در `config/settings.py`:
  - `REST_FRAMEWORK`: احراز هویت JWT، مجوز پیش‌فرض `IsAuthenticated`، و `drf_spectacular` برای طرح‌واره OpenAPI
  - `SIMPLE_JWT`: طول عمر توکن‌ها، الگوریتم و نوع هدر
  - کلیدهای AI: `GAPGPT_API_KEY`, `OPENAI_API_KEY` (اختیاری)

## 🧪 تست‌ها

- اجرای تست‌ها: `pytest -v`
- تست‌ها شامل بررسی مسیرهای API (health/schema/docs)، JWT، اندپوینت‌های نسخه‌بندی و جریان‌های پایه است.

## 📁 ساختار پروژه (خلاصه)

```bash
config/        تنظیمات پروژه و URLها
gateway/       ثبت روترها و اندپوینت‌های سطح ریشهٔ API
gitdm/         دامنهٔ اصلی (کاربر/بیمار) و ViewSetهای مرتبط
encounters/    مواجهه‌های بالینی
intelligence/  خلاصه‌سازی مبتنی بر AI و اکشن‌های مرتبط
laboratory/    نتایج آزمایشگاه
pharmacy/      دستورات دارویی
references/    مراجع بالینی
versioning/    API نسخه‌بندی تغییرات رکوردها
security/      اجزای امنیتی/ادمین
tests/         مجموعهٔ تست (pytest / pytest-django)
```

## 📜 مجوز

این پروژه تحت مجوز موجود در فایل `LICENSE` منتشر شده است.

## 🤝 مشارکت در توسعه

- تست‌ها را پیش از ارسال PR اجرا کنید: `pytest -v`
- پیام‌های کامیت کوتاه و شفاف باشند؛ PRها متمرکز و کوچک ارسال شوند.
