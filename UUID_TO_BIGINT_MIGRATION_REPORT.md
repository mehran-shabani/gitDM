# گزارش تغییرات مایگریشن از UUID به BigAutoField

## خلاصه اجرایی
این پروژه برای استفاده از UUID به عنوان Primary Key در مدل‌ها پیکربندی شده بود. طبق درخواست، تمامی فیلدهای UUID حذف و از سیستم ID پیش‌فرض Django (BigAutoField) استفاده شد.

## تغییرات انجام شده

### 1. حذف UUID از مدل‌ها
تمامی مدل‌های زیر از UUID به BigAutoField تغییر یافتند:

#### patients_core/models.py (Patient)
```python
# قبل:
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

# بعد:
# ID field removed - Django will use default BigAutoField
```

#### diab_encounters/models.py (Encounter)
```python
# قبل:
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

# بعد:
# ID field removed - Django will use default BigAutoField
```

#### diab_labs/models.py (LabResult)
```python
# قبل:
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

# بعد:
# ID field removed - Django will use default BigAutoField
```

#### diab_medications/models.py (MedicationOrder)
```python
# قبل:
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

# بعد:
# ID field removed - Django will use default BigAutoField
```

#### clinical_refs/models.py (ClinicalReference)
```python
# قبل:
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

# بعد:
# ID field removed - Django will use default BigAutoField
```

#### ai_summarizer/models.py (AISummary)
```python
# قبل:
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
object_id = models.UUIDField()

# بعد:
# ID field removed - Django will use default BigAutoField
object_id = models.PositiveIntegerField()
```

### 2. به‌روزرسانی Foreign Key References

#### records_versioning/models.py (RecordVersion)
```python
# قبل:
resource_id = models.UUIDField()

# بعد:
resource_id = models.PositiveIntegerField()
```

### 3. به‌روزرسانی Serializers

#### api/serializers.py
```python
# قبل:
primary_doctor_id = serializers.UUIDField(source='primary_doctor.id', read_only=True)

# بعد:
primary_doctor_id = serializers.IntegerField(source='primary_doctor.id', read_only=True)
```

همچنین فیلد `route` که در مدل MedicationOrder وجود نداشت از سریالایزر حذف شد.

### 4. به‌روزرسانی URL Patterns

#### api/routers.py
```python
# قبل:
path('versions/<str:resource_type>/<uuid:resource_id>/', ...)

# بعد:
path('versions/<str:resource_type>/<int:resource_id>/', ...)
```

### 5. حذف تنظیمات اضافی

#### config/settings.py
- حذف `SYSTEM_USER_ID = '00000000-0000-0000-0000-000000000001'`
- حذف تنظیمات تکراری `SPECTACULAR_SETTINGS`

### 6. به‌روزرسانی Views

#### api/views.py
- حذف import `from uuid import UUID`
- تغییر منطق `SYSTEM_USER_ID` به استفاده از یک کاربر سیستمی با username='system'
- سیستم حالا به جای UUID ثابت، یک کاربر سیستمی ایجاد می‌کند یا از کاربر موجود استفاده می‌کند

### 7. رفع مشکلات Indentation
فایل `diab_encounters/models.py` دارای مشکلات indentation بود که اصلاح شد.

## API های احراز هویت

API های لاگین برای دریافت توکن JWT بررسی شدند و به درستی پیکربندی شده‌اند:

- `POST /api/token/` - دریافت access و refresh token
- `POST /api/token/refresh/` - تازه‌سازی access token

این endpoints از `rest_framework_simplejwt` استفاده می‌کنند و نیازی به ایجاد API جدید نبود.

## نکات مهم برای مایگریشن

### ⚠️ هشدار: این تغییرات Breaking Changes هستند

1. **از دست رفتن داده‌ها**: تغییر از UUID به Integer باعث از دست رفتن ID های موجود خواهد شد
2. **مایگریشن‌های جدید**: باید تمام مایگریشن‌های قدیمی حذف و مایگریشن‌های جدید ایجاد شوند
3. **وابستگی‌های خارجی**: اگر سیستم‌های خارجی به UUID ها وابسته هستند، باید به‌روزرسانی شوند

### دستورات مایگریشن پیشنهادی

```bash
# حذف مایگریشن‌های قدیمی
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete

# ایجاد مایگریشن‌های جدید
python manage.py makemigrations

# اعمال مایگریشن‌ها (در محیط جدید بدون داده)
python manage.py migrate
```

## تناقضات و راه‌حل‌ها

### 1. وابستگی به UUID در سیستم‌های خارجی
**مشکل**: ممکن است سیستم‌های خارجی یا API های موجود به UUID ها وابسته باشند.
**راه‌حل**: از Integer ID استفاده شد و برای سازگاری می‌توان یک فیلد UUID اضافی غیر Primary Key در آینده اضافه کرد.

### 2. Generic Foreign Key در AISummary
**مشکل**: `object_id` در `AISummary` برای Generic Foreign Key از UUID به Integer تغییر یافت.
**راه‌حل**: فیلد به `PositiveIntegerField` تغییر یافت که با ID های جدید سازگار است.

### 3. سیستم کاربر پیش‌فرض
**مشکل**: `SYSTEM_USER_ID` به صورت UUID ثابت تعریف شده بود.
**راه‌حل**: به جای UUID ثابت، سیستم یک کاربر با username='system' ایجاد یا استفاده می‌کند.

## توصیه‌های امنیتی

1. کاربر سیستمی با `is_active=False` ایجاد می‌شود تا نتوان با آن لاگین کرد
2. احراز هویت JWT به درستی پیکربندی شده و نیاز به توکن معتبر دارد
3. تمام ViewSet ها دارای `permission_classes = [IsAuthenticated]` هستند

## نتیجه‌گیری

تمامی تغییرات درخواستی با موفقیت انجام شد:
- ✅ حذف کامل UUID از مدل‌ها
- ✅ استفاده از BigAutoField پیش‌فرض Django
- ✅ بررسی و تأیید API های احراز هویت
- ✅ حذف تنظیمات اضافی و تکراری
- ✅ به‌روزرسانی تمام وابستگی‌ها به Integer ID

پروژه اکنون از سیستم ID استاندارد Django استفاده می‌کند که ساده‌تر، سریع‌تر و سازگارتر با اکوسیستم Django است.