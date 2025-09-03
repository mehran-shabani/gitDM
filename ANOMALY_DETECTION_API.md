# راهنمای API سیستم تشخیص الگوهای غیرطبیعی

## مقدمه

سیستم تشخیص الگوهای غیرطبیعی GitDM قابلیت تحلیل هوشمند داده‌های تاریخی بیماران و شناسایی ناهنجاری‌های آماری و الگویی را فراهم می‌کند. این سیستم شامل چهار بخش اصلی است:

1. **معیارهای پایه (Baseline Metrics)**: محاسبه و ذخیره آمار پایه هر بیمار
2. **تحلیل الگو (Pattern Analysis)**: تحلیل روندها و الگوهای رفتاری
3. **تشخیص ناهنجاری (Anomaly Detection)**: شناسایی مقادیر غیرطبیعی
4. **هشدارهای الگویی (Pattern Alerts)**: ایجاد هشدارهای هوشمند

---

## 🔧 راه‌اندازی

### 1. اجرای Migration
```bash
python manage.py migrate intelligence
```

### 2. وابستگی‌های مورد نیاز
- `numpy>=1.24.0` (اضافه شده به requirements.txt)
- `openai>=1.65.0` (برای تحلیل‌های AI)

### 3. تنظیمات
تمام تنظیمات پیش‌فرض مناسب هستند. در صورت نیاز می‌توانید آستانه‌های تشخیص را در `AnomalyDetectionService` تنظیم کنید.

---

## 📊 API Endpoints

### معیارهای پایه (Baseline Metrics)

#### `GET /api/baseline-metrics/`
دریافت لیست معیارهای پایه

**پارامترهای Query:**
- `patient_id`: فیلتر بر اساس شناسه بیمار

**نمونه پاسخ:**
```json
{
    "count": 1,
    "results": [
        {
            "patient": 123,
            "avg_hba1c": "7.20",
            "avg_blood_glucose": "145.50",
            "std_hba1c": "0.80",
            "std_blood_glucose": "25.30",
            "avg_encounters_per_month": "2.50",
            "avg_labs_per_month": "1.80",
            "last_calculated": "2024-01-15T10:30:00Z",
            "data_points_count": 24
        }
    ]
}
```

#### `POST /api/baseline-metrics/calculate/`
محاسبه معیارهای پایه برای بیمار

**پارامترهای ورودی:**
```json
{
    "patient_id": 123,
    "months_back": 12
}
```

---

### تحلیل الگو (Pattern Analysis)

#### `GET /api/pattern-analyses/`
دریافت لیست تحلیل‌های الگو

**پارامترهای Query:**
- `patient_id`: فیلتر بر اساس بیمار
- `pattern_type`: نوع الگو (`GLUCOSE_TREND`, `MEDICATION_ADHERENCE`, ...)

#### `POST /api/pattern-analyses/analyze/`
درخواست تحلیل جدید

**پارامترهای ورودی:**
```json
{
    "patient_id": 123,
    "pattern_types": ["GLUCOSE_TREND", "MEDICATION_ADHERENCE"],
    "months_back": 6
}
```

**نمونه پاسخ:**
```json
{
    "status": "success",
    "analyses_created": 2,
    "results": [
        {
            "id": 45,
            "patient": 123,
            "pattern_type": "GLUCOSE_TREND",
            "pattern_type_display": "روند قند خون",
            "trend_direction": "WORSENING",
            "trend_direction_display": "بدتر شدن",
            "analysis_result": {
                "slope": 8.5,
                "r_squared": 0.85,
                "mean_value": 155.2,
                "data_points": 12,
                "trend_description": "بدتر شدن با نرخ 8.5 واحد در ماه"
            },
            "confidence_score": "0.85",
            "created_at": "2024-01-15T14:20:00Z"
        }
    ]
}
```

---

### تشخیص ناهنجاری (Anomaly Detection)

#### `GET /api/anomaly-detections/`
دریافت لیست ناهنجاری‌ها

**پارامترهای Query:**
- `patient_id`: فیلتر بر اساس بیمار
- `severity`: سطح شدت (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
- `acknowledged`: وضعیت تایید (`true`/`false`)

**نمونه پاسخ:**
```json
{
    "count": 3,
    "results": [
        {
            "id": 78,
            "patient": 123,
            "anomaly_type": "STATISTICAL_OUTLIER",
            "anomaly_type_display": "نقطه پرت آماری",
            "severity_level": "HIGH",
            "severity_level_display": "بالا",
            "description": "مقدار glucose (280) به طور قابل توجهی از میانگین (145.50) منحرف است",
            "detected_value": "280.00",
            "expected_value": "145.50",
            "deviation_score": "3.200",
            "is_acknowledged": false,
            "detected_at": "2024-01-15T16:45:00Z",
            "data_timestamp": "2024-01-15T16:40:00Z"
        }
    ]
}
```

#### `POST /api/anomaly-detections/{id}/acknowledge/`
تایید ناهنجاری

**پارامترهای ورودی:**
```json
{
    "notes": "بررسی شد، مقدار بعد از غذا بوده است"
}
```

---

### هشدارهای الگویی (Pattern Alerts)

#### `GET /api/pattern-alerts/`
دریافت لیست هشدارهای الگویی

**پارامترهای Query:**
- `patient_id`: فیلتر بر اساس بیمار
- `priority`: اولویت (`LOW`, `MEDIUM`, `HIGH`, `URGENT`)
- `active_only`: فقط هشدارهای فعال (`true`/`false`)

**نمونه پاسخ:**
```json
{
    "count": 2,
    "results": [
        {
            "id": 12,
            "patient": 123,
            "alert_type": "DETERIORATING_CONTROL",
            "alert_type_display": "بدتر شدن کنترل",
            "priority": "HIGH",
            "priority_display": "بالا",
            "title": "روند نامطلوب قند خون در بیمار احمد محمدی",
            "message": "تحلیل الگوهای رفتاری نشان می‌دهد که وضعیت بیمار در حال بدتر شدن است...",
            "related_patterns_count": 1,
            "related_anomalies_count": 3,
            "is_active": true,
            "is_resolved": false,
            "created_at": "2024-01-15T17:00:00Z",
            "expires_at": "2024-01-22T17:00:00Z"
        }
    ]
}
```

#### `POST /api/pattern-alerts/{id}/resolve/`
حل هشدار

**پارامترهای ورودی:**
```json
{
    "resolution_notes": "با بیمار تماس گرفته شد و برنامه درمانی تنظیم شد"
}
```

---

## 🔄 گردش کار خودکار

### 1. هنگام ثبت نتیجه آزمایش جدید:
1. Signal خودکار فعال می‌شود
2. تسک `run_anomaly_detection_for_new_lab` اجرا می‌شود
3. ناهنجاری‌های آماری و تغییرات ناگهانی بررسی می‌شوند
4. در صورت تشخیص، ناهنجاری ثبت می‌شود

### 2. هنگام ثبت مواجهه جدید:
1. Signal خودکار فعال می‌شود
2. تسک `run_pattern_analysis_for_patient` اجرا می‌شود
3. الگوهای پایبندی دارویی و فراوانی ویزیت بررسی می‌شوند
4. در صورت تشخیص مشکل، هشدار ایجاد می‌شود

### 3. تحلیل روزانه:
- تسک `run_daily_pattern_analysis` برای تمام بیماران فعال اجرا می‌شود
- الگوهای جدید شناسایی و هشدارهای مربوطه ایجاد می‌شوند

---

## 📈 الگوریتم‌های تحلیلی

### 1. تشخیص نقاط پرت (Z-Score Analysis)
```
Z-Score = |مقدار_جدید - میانگین| / انحراف_معیار

آستانه‌ها:
- کم: Z-Score ≥ 2.0
- متوسط: Z-Score ≥ 2.5  
- بالا: Z-Score ≥ 3.0
- بحرانی: Z-Score ≥ 3.5
```

### 2. تشخیص تغییرات ناگهانی
```
درصد_تغییر = |مقدار_جدید - مقدار_قبلی| / مقدار_قبلی * 100

آستانه‌ها:
- کم: تغییر ≥ 25%
- متوسط: تغییر ≥ 30%
- بالا: تغییر ≥ 40%
- بحرانی: تغییر ≥ 50%
```

### 3. تحلیل روند خطی
- استفاده از رگرسیون خطی ساده
- محاسبه شیب روند (واحد بر ماه)
- محاسبه ضریب تعیین (R²) برای اطمینان

### 4. تحلیل پایبندی دارویی
```
امتیاز_پایبندی = تعداد_ویزیت_واقعی / تعداد_ویزیت_مورد_انتظار

معیار انتظار: 2 ویزیت فالوآپ برای هر دارو
```

---

## ⚙️ تنظیمات پیشرفته

### آستانه‌های تشخیص ناهنجاری
در `intelligence/services.py`:

```python
class AnomalyDetectionService:
    Z_SCORE_THRESHOLDS = {
        'LOW': 2.0,
        'MEDIUM': 2.5,
        'HIGH': 3.0,
        'CRITICAL': 3.5
    }
```

### کدهای LOINC پشتیبانی شده
- **HbA1c**: `4548-4`, `17856-6`
- **قند خون**: `2345-7`, `2339-0`, `1558-6`

---

## 🚨 نمونه‌های کاربردی

### 1. نظارت بر بیمار با کنترل ضعیف
```bash
# محاسبه baseline
curl -X POST /api/baseline-metrics/calculate/ \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"patient_id": 123, "months_back": 12}'

# تحلیل روند قند خون
curl -X POST /api/pattern-analyses/analyze/ \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"patient_id": 123, "pattern_types": ["GLUCOSE_TREND"], "months_back": 6}'

# بررسی هشدارهای فعال
curl -X GET "/api/pattern-alerts/?patient_id=123&active_only=true" \
  -H "Authorization: Bearer <TOKEN>"
```

### 2. پیگیری ناهنجاری‌های بحرانی
```bash
# دریافت ناهنجاری‌های بحرانی
curl -X GET "/api/anomaly-detections/?severity=CRITICAL&acknowledged=false" \
  -H "Authorization: Bearer <TOKEN>"

# تایید ناهنجاری پس از بررسی
curl -X POST /api/anomaly-detections/78/acknowledge/ \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"notes": "با بیمار تماس گرفته شد، مشکل حل شد"}'
```

### 3. مدیریت هشدارهای اولویت بالا
```bash
# دریافت هشدارهای فوری
curl -X GET "/api/pattern-alerts/?priority=URGENT&active_only=true" \
  -H "Authorization: Bearer <TOKEN>"

# حل هشدار
curl -X POST /api/pattern-alerts/12/resolve/ \
  -H "Authorization: Bearer <TOKEN>" \
  -d '{"resolution_notes": "برنامه درمانی تغییر کرد و بیمار آموزش داده شد"}'
```

---

## 📝 ساختار داده‌ها

### BaselineMetrics
```json
{
    "patient": 123,
    "avg_hba1c": "7.20",
    "std_hba1c": "0.80",
    "avg_blood_glucose": "145.50", 
    "std_blood_glucose": "25.30",
    "avg_encounters_per_month": "2.50",
    "avg_labs_per_month": "1.80",
    "medication_adherence_score": "0.85",
    "last_calculated": "2024-01-15T10:30:00Z",
    "data_points_count": 24
}
```

### PatternAnalysis
```json
{
    "id": 45,
    "patient": 123,
    "pattern_type": "GLUCOSE_TREND",
    "trend_direction": "WORSENING",
    "analysis_result": {
        "slope": 8.5,
        "r_squared": 0.85,
        "mean_value": 155.2,
        "data_points": 12
    },
    "confidence_score": "0.85",
    "analysis_start_date": "2023-07-15T00:00:00Z",
    "analysis_end_date": "2024-01-15T00:00:00Z"
}
```

### AnomalyDetection
```json
{
    "id": 78,
    "patient": 123,
    "anomaly_type": "STATISTICAL_OUTLIER",
    "severity_level": "HIGH",
    "description": "مقدار glucose (280) به طور قابل توجهی از میانگین (145.50) منحرف است",
    "detected_value": "280.00",
    "expected_value": "145.50",
    "deviation_score": "3.200",
    "is_acknowledged": false,
    "detected_at": "2024-01-15T16:45:00Z"
}
```

### PatternAlert
```json
{
    "id": 12,
    "patient": 123,
    "alert_type": "DETERIORATING_CONTROL",
    "priority": "HIGH",
    "title": "روند نامطلوب قند خون در بیمار احمد محمدی",
    "message": "تحلیل الگوهای رفتاری نشان می‌دهد...",
    "related_patterns_count": 1,
    "related_anomalies_count": 3,
    "is_active": true,
    "is_resolved": false,
    "created_at": "2024-01-15T17:00:00Z"
}
```

---

## 🔍 انواع الگوها و ناهنجاری‌ها

### انواع الگو (PatternType):
- `GLUCOSE_TREND`: روند قند خون
- `HBA1C_TREND`: روند HbA1c
- `BP_TREND`: روند فشار خون
- `MEDICATION_ADHERENCE`: پایبندی دارویی
- `VISIT_FREQUENCY`: فراوانی ویزیت
- `LAB_FREQUENCY`: فراوانی آزمایش

### انواع ناهنجاری (AnomalyType):
- `STATISTICAL_OUTLIER`: نقطه پرت آماری
- `SUDDEN_CHANGE`: تغییر ناگهانی
- `TREND_REVERSAL`: معکوس شدن روند
- `MISSING_DATA`: داده گمشده
- `MEDICATION_SKIP`: عدم مصرف دارو
- `UNUSUAL_PATTERN`: الگوی غیرعادی

### انواع هشدار (AlertType):
- `DETERIORATING_CONTROL`: بدتر شدن کنترل
- `MEDICATION_NON_ADHERENCE`: عدم پایبندی دارویی
- `MISSED_APPOINTMENTS`: عدم حضور در ویزیت
- `UNUSUAL_LAB_PATTERN`: الگوی غیرعادی آزمایش
- `EMERGENCY_PATTERN`: الگوی اورژانسی

---

## 🎯 بهترین شیوه‌های استفاده

### 1. محاسبه اولیه Baseline
قبل از شروع تحلیل، حتماً baseline metrics را محاسبه کنید:
```bash
POST /api/baseline-metrics/calculate/
```

### 2. تحلیل دوره‌ای
برای نتایج بهتر، تحلیل الگو را هر 2-4 هفته انجام دهید:
```bash
POST /api/pattern-analyses/analyze/
```

### 3. پیگیری هشدارها
هشدارهای فعال را روزانه بررسی کنید:
```bash
GET /api/pattern-alerts/?active_only=true&priority=HIGH
```

### 4. تایید ناهنجاری‌ها
ناهنجاری‌های تشخیص داده شده را پس از بررسی تایید کنید:
```bash
POST /api/anomaly-detections/{id}/acknowledge/
```

---

## ⚡ عملکرد و بهینه‌سازی

### 1. Indexing
تمام فیلدهای مهم دارای index هستند:
- جستجو بر اساس بیمار
- فیلتر بر اساس تاریخ
- فیلتر بر اساس شدت و اولویت

### 2. Background Processing
تمام تحلیل‌های سنگین در پس‌زمینه اجرا می‌شوند:
- استفاده از Celery برای تسک‌های ناهمزمان
- پردازش خودکار با Signals

### 3. Caching
نتایج تحلیل‌ها ذخیره می‌شوند و مجدداً محاسبه نمی‌شوند مگر در صورت تغییر داده‌ها.

---

## 🔧 عیب‌یابی

### مشکلات رایج:

1. **خطای "Baseline not found"**
   - ابتدا `/api/baseline-metrics/calculate/` را اجرا کنید

2. **تحلیل الگو نتیجه نمی‌دهد**
   - حداقل 3 نقطه داده در بازه زمانی مورد نظر لازم است

3. **Celery tasks اجرا نمی‌شوند**
   - اطمینان حاصل کنید که Celery worker فعال است
   - در محیط توسعه، تسک‌ها synchronous اجرا می‌شوند

### لاگ‌ها:
تمام عملیات در `intelligence` logger ثبت می‌شوند:
```python
import logging
logger = logging.getLogger('intelligence')
```

---

## 📋 چک‌لیست راه‌اندازی

- [ ] Migration اجرا شده است
- [ ] numpy نصب شده است  
- [ ] Baseline metrics برای بیماران محاسبه شده است
- [ ] Celery worker فعال است (اختیاری)
- [ ] تست‌های API موفق هستند
- [ ] پنل ادمین برای مشاهده داده‌ها تنظیم شده است

---

**توجه**: این سیستم به صورت کامل با سایر بخش‌های GitDM یکپارچه شده و از همان سیستم احراز هویت، مجوزها و audit logging استفاده می‌کند.