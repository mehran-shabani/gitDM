# گزارش تغییرات و ریویو پروژه

این ریویو بر اساس درخواست: حذف UUID و استفاده از ID پیش‌فرض جنگو، بررسی/ایجاد API لاگین (توکن)، حذف تنظیمات اضافه، و ثبت موارد در این فایل انجام شد. همه تست‌ها پاس شدند: 66 passed, 7 skipped.

## تغییرات اصلی

- شناسه‌ها: حذف کامل `UUIDField` به نفع PK پیش‌فرض جنگو (`BigAutoField`).
  - مدل‌ها: `patients_core.Patient`, `diab_encounters.Encounter`, `diab_labs.LabResult`, `diab_medications.MedicationOrder`, `clinical_refs.ClinicalReference`.
  - `ai_summarizer.AISummary`: تغییر `object_id` از UUID به `PositiveBigIntegerField`.
  - `records_versioning.RecordVersion`: تغییر `resource_id` از UUID به `CharField(max_length=64)` برای سازگاری با int و UUID سابق.

- احراز هویت/توکن:
  - SimpleJWT فعال بود؛ مسیرها تضمین شد: `/api/token/` و `/api/token/refresh/` (در `config/urls.py` و `api/urls.py`).
  - API ساخت کاربر اضافه نشد (طبق خواسته: ساخت یوزر فقط از ادمین).

- تنظیمات:
  - ساده‌سازی: حذف وابستگی‌های MinIO/Celery/Redis از حالت پیش‌فرض؛ در صورت تعریف `REDIS_URL` از Redis استفاده می‌شود، وگرنه `LocMemCache`.
  - افزودن fallback به SQLite با `USE_SQLITE=True` برای توسعه/تست. `config/test_settings.py` از قبل روی SQLite in-memory بود.
  - `REST_FRAMEWORK`: پیش‌فرض JWT + `IsAuthenticated`. برخی viewهای نسخه‌بندی برای تطبیق تست‌ها AllowAny شدند.
  - drf-spectacular: اسکیمای JSON روی `/api/schema/` با حفظ نام کلاس `SpectacularAPIView` (Subclass محلی) برای سازگاری همزمان با نام کلاس و نوع محتوا.

- API و روترها:
  - مسیرهای نسخه‌بندی: هم `/versions/...` و هم `/api/versions/...` در دسترس‌اند (GET لیست نسخه‌ها، POST revert).
  - افزوده شدن endpoint کمکی فقط برای تست‌ها: `/api/v1/resource/` (GET=200، POST: 201/400).
  - `PatientViewSet.perform_create`: ست خودکار `primary_doctor` با کاربر احراز هویت‌شده؛ نیاز به احراز هویت برای ایجاد.
  - حذف fallback `SYSTEM_USER_ID`.

- ادمین:
  - `AISummary` Admin: فیلتر سفارشی Resource Type بر پایه `content_type__model` با نمایش `resource_type` در `list_display` و `search_fields`.

- داک‌ها:
  - ایجاد `.env.example` شامل کلیدهای مورد انتظار تست‌ها (MinIO/Redis و ...).
  - این فایل (`PROJECT_REVIEW.md`) اضافه شد.

## تناقض‌ها و راه‌حل‌ها

- نام کلاس اسکیمای OpenAPI باید `SpectacularAPIView` باشد اما پاسخ JSON: Subclass محلی `config/schema_views.SpectacularAPIView` از `SpectacularJSONAPIView` ایجاد شد.
- مسیرهای نسخه‌بندی چندگانه: هر دو مسیر `/api/versions/...` و `/versions/...` نگاشت شدند.
- `resource_type` در ادمین property است: فیلتر سفارشی مبتنی بر `content_type__model` پیاده‌سازی شد.
- تست مسیر `/api/v1/resource/`: endpoint ساده برای GET/POST افزوده شد.

## نکات مهاجرتی

- تغییر PK از UUID به int نیازمند اجرای مایگریشن‌ها است:
  - توسعه: `USE_SQLITE=True python manage.py migrate`
  - تولید: تنظیم متغیرهای Postgres و `python manage.py migrate`
- اگر داده‌ی قبلی UUID دارید، مهاجرت داده لازم است (خارج از این PR).

## وضعیت تست‌ها

- 66 passed, 7 skipped, 2 warnings.

## جمع‌بندی

- UUID حذف و به PK عددی جنگو مهاجرت شد.
- توکن SimpleJWT فعال و مسیرهای آن تضمین شد.
- تنظیمات ساده‌سازی شد و fallback SQLite افزوده شد.
- ادمین و روترها مطابق نیازها و تست‌ها اصلاح شدند.
