# داشبورد تحلیلی پیشرفته GitDM

## نمای کلی

ماژول Analytics یک داشبورد تحلیلی پیشرفته برای سیستم مدیریت دیابت GitDM ارائه می‌دهد که شامل نمودارهای تعاملی، آمار پیشرفته و گزارش‌گیری خودکار است.

## ویژگی‌های کلیدی

### 1. **نمودارهای تعاملی**
- نمودار روند قند خون (FBS, RBS, PPBS)
- نمودار روند HbA1c
- نمودار توزیع بیماران بر اساس کنترل دیابت
- نمودارهای مقایسه‌ای عملکرد

### 2. **آمار پیشرفته**
- محاسبه میانگین، انحراف معیار، حداقل و حداکثر
- تحلیل روندها (بهبود، ثابت، بدتر شدن)
- امتیاز پایبندی به درمان
- امتیاز عملکرد پزشک

### 3. **گزارش‌گیری خودکار**
- گزارش خلاصه بیمار (PDF/Excel/CSV)
- گزارش عملکرد پزشک
- گزارش نمای کلی سیستم
- گزارش‌های زمان‌بندی شده (روزانه، هفتگی، ماهانه)

## ساختار پروژه

```
analytics/
├── models.py           # مدل‌های داده برای ذخیره آمارها
├── serializers.py      # سریالایزرهای DRF
├── views.py           # API endpoints
├── services.py        # سرویس‌های تحلیل داده
├── report_service.py  # سرویس تولید گزارش
├── tasks.py          # Celery tasks برای پردازش‌های پس‌زمینه
├── urls.py           # مسیریابی URL
├── admin.py          # تنظیمات پنل ادمین
├── tests.py          # تست‌های واحد
├── templates/        # قالب‌های HTML
├── static/           # فایل‌های استاتیک (CSS, JS)
└── README.md         # این فایل
```

## API Endpoints

### آنالیتیکس بیماران
```
GET  /api/analytics/patient-analytics/          # لیست آنالیتیکس بیماران
POST /api/analytics/patient-analytics/calculate/ # محاسبه آنالیتیکس جدید
GET  /api/analytics/patient-analytics/{id}/glucose_chart/  # نمودار قند خون
GET  /api/analytics/patient-analytics/{id}/hba1c_trend/    # روند HbA1c
```

### آنالیتیکس پزشکان
```
GET  /api/analytics/doctor-analytics/           # لیست آنالیتیکس پزشکان
POST /api/analytics/doctor-analytics/calculate/ # محاسبه آنالیتیکس پزشک
GET  /api/analytics/doctor-analytics/{id}/patient_distribution/ # توزیع بیماران
```

### آنالیتیکس سیستم
```
GET  /api/analytics/system-analytics/          # آمارهای سیستم
GET  /api/analytics/system-analytics/overview/ # نمای کلی
GET  /api/analytics/system-analytics/trend_chart/ # نمودار روند
```

### گزارش‌ها
```
GET  /api/analytics/reports/              # لیست گزارش‌ها
POST /api/analytics/reports/              # ایجاد گزارش جدید
GET  /api/analytics/reports/{id}/download/ # دانلود گزارش
POST /api/analytics/reports/{id}/send_email/ # ارسال ایمیل
```

### داشبورد
```
GET  /api/analytics/dashboard/summary/    # خلاصه داشبورد
GET  /api/analytics/dashboard/widgets/    # ویجت‌های داشبورد
```

## نحوه استفاده

### 1. نصب وابستگی‌ها
```bash
pip install -r requirements.txt
```

### 2. اجرای میگریشن‌ها
```bash
python manage.py makemigrations analytics
python manage.py migrate
```

### 3. جمع‌آوری فایل‌های استاتیک
```bash
python manage.py collectstatic
```

### 4. دسترسی به داشبورد
داشبورد در آدرس زیر قابل دسترسی است:
```
http://localhost:8000/analytics/dashboard/
```

## مدل‌های داده

### PatientAnalytics
ذخیره آمارهای تحلیلی بیماران شامل:
- میانگین، حداقل و حداکثر قند خون
- میانگین HbA1c
- روند قند خون و HbA1c
- تعداد ویزیت‌ها، آزمایش‌ها و داروها
- امتیاز پایبندی به درمان

### DoctorAnalytics
ذخیره آمارهای عملکرد پزشکان شامل:
- تعداد کل و فعال بیماران
- میانگین HbA1c بیماران
- تعداد بیماران در محدوده هدف
- امتیاز عملکرد

### SystemAnalytics
ذخیره آمارهای کلی سیستم شامل:
- تعداد کاربران و بیماران
- میانگین HbA1c سیستم
- درصد دستیابی به اهداف
- آمار استفاده از API

## سرویس‌های تحلیل

### PatientAnalyticsService
- محاسبه آمارهای بیمار
- تولید داده‌های نمودار قند خون
- تولید داده‌های روند HbA1c
- محاسبه امتیاز پایبندی

### DoctorAnalyticsService
- محاسبه آمارهای پزشک
- تولید نمودار توزیع بیماران
- محاسبه امتیاز عملکرد

### SystemAnalyticsService
- محاسبه آمارهای سیستم
- تولید نمای کلی داشبورد
- تولید نمودارهای روند

## گزارش‌گیری

### انواع گزارش
1. **خلاصه بیمار**: شامل تاریخچه کامل، آزمایش‌ها، داروها و نمودارها
2. **عملکرد پزشک**: آمار بیماران، نتایج درمان و امتیاز عملکرد
3. **نمای کلی سیستم**: آمارهای کلی و روندهای سیستم

### فرمت‌های خروجی
- PDF: با پشتیبانی از فونت فارسی
- Excel: با چند برگه و قالب‌بندی
- CSV: برای تحلیل‌های بیشتر

### گزارش‌های زمان‌بندی شده
- گزارش‌های روزانه: محاسبه آنالیتیکس
- گزارش‌های هفتگی: نمای کلی سیستم برای ادمین‌ها
- گزارش‌های ماهانه: عملکرد پزشکان

## Celery Tasks

### calculate_daily_analytics
محاسبه آنالیتیکس روزانه برای همه بیماران و پزشکان (ساعت 2 صبح)

### generate_scheduled_reports
تولید گزارش‌های زمان‌بندی شده (ساعت 8 صبح)

### cleanup_old_analytics
پاکسازی داده‌های قدیمی‌تر از یک سال (یکشنبه‌ها)

### check_critical_values
بررسی مقادیر بحرانی و ایجاد هشدار (هر 30 دقیقه)

## تنظیمات امنیتی

- تمام API endpoints نیاز به احراز هویت دارند
- پزشکان فقط به داده‌های بیماران خود دسترسی دارند
- ادمین‌ها به همه داده‌ها دسترسی دارند
- گزارش‌ها فقط توسط درخواست‌دهنده قابل دسترسی هستند

## نکات توسعه

### اضافه کردن نمودار جدید
1. سرویس تحلیل را در `services.py` اضافه کنید
2. Endpoint را در `views.py` تعریف کنید
3. کامپوننت JavaScript را در `dashboard.js` اضافه کنید

### اضافه کردن متریک جدید
1. فیلد را به مدل مناسب اضافه کنید
2. منطق محاسبه را در سرویس پیاده‌سازی کنید
3. سریالایزر را بروزرسانی کنید

### اضافه کردن نوع گزارش جدید
1. نوع را به `REPORT_TYPES` اضافه کنید
2. متد تولید را در `ReportGenerationService` پیاده‌سازی کنید
3. قالب PDF/Excel را ایجاد کنید

## عیب‌یابی

### خطای import
```bash
# بررسی نصب وابستگی‌ها
pip install numpy pandas matplotlib reportlab openpyxl
```

### خطای میگریشن
```bash
# حذف میگریشن‌های قبلی و ایجاد مجدد
rm analytics/migrations/0*.py
python manage.py makemigrations analytics
python manage.py migrate
```

### نمودارها نمایش داده نمی‌شوند
- بررسی کنید که Chart.js بارگذاری شده باشد
- کنسول مرورگر را برای خطاهای JavaScript بررسی کنید
- مطمئن شوید که API داده‌ها را برمی‌گرداند

## مشارکت

برای مشارکت در توسعه:
1. Fork کنید
2. Branch جدید ایجاد کنید (`git checkout -b feature/amazing-feature`)
3. تغییرات را Commit کنید (`git commit -m 'Add amazing feature'`)
4. Push کنید (`git push origin feature/amazing-feature`)
5. Pull Request ایجاد کنید

## لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.