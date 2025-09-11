# Timeline App - سیستم تایم‌لاین پزشکی

این اپلیکیشن سیستم جامعی برای مدیریت تایم‌لاین پزشکی و یادآورهای آزمایشات در سامانه GitDM فراهم می‌کند.

## ویژگی‌ها

### 1. تایم‌لاین پزشکی (MedicalTimeline)
- ثبت خودکار تمام رویدادهای پزشکی در یک خط زمان واحد
- پشتیبانی از انواع مختلف رویدادها:
  - مواجهات بالینی (ENCOUNTER)
  - نتایج آزمایش (LAB_RESULT)  
  - داروها (MEDICATION)
  - معاینات فیزیکی (PHYSICAL_EXAM)
  - هشدارهای بالینی (ALERT)
  - یادآورها (REMINDER)

### 2. سیستم یادآوری آزمایشات (TestReminder)
- یادآورهای هوشمند برای آزمایشات دوره‌ای
- پشتیبانی از آزمایشات مختلف:
  - **آزمایشات خونی**: HbA1c, FBS, 2HPP, BUN, Creatinine, ALT, AST, ALP, TSH
  - **آزمایش ادرار**: پروتئین ۲۴ ساعته
  - **معاینات**: چشم، EMG، NCV
  - **اندازه‌گیری‌ها**: BMI، فشار خون
  - **مشاوره‌ها**: تغذیه، ورزش

### 3. نمودار تعاملی
- نمایش گرافیکی تایم‌لاین با Chart.js
- فیلتر بر اساس تاریخ، نوع رویداد، شدت
- نمایش جزئیات با hover
- قابلیت چاپ و خروجی PDF

## نصب و راه‌اندازی

### 1. اضافه کردن به INSTALLED_APPS
```python
INSTALLED_APPS = [
    # ...
    'timeline',
    # ...
]
```

### 2. اجرای Migration
```bash
python manage.py makemigrations timeline
python manage.py migrate
```

### 3. ایجاد قالب‌های یادآوری
```bash
python manage.py create_reminder_templates
```

### 4. ایجاد داده‌های نمونه (اختیاری)
```bash
python manage.py create_sample_timeline --patient-id=1
```

## API Endpoints

### Timeline APIs
- `GET /timeline/api/timeline/` - لیست رویدادهای تایم‌لاین
- `GET /timeline/api/timeline/patient_timeline/?patient_id=X` - تایم‌لاین بیمار خاص
- `GET /timeline/api/timeline/timeline_summary/?patient_id=X` - خلاصه تایم‌لاین

### Reminder APIs  
- `GET /timeline/api/reminders/` - لیست یادآورها
- `GET /timeline/api/reminders/patient_reminders/?patient_id=X` - یادآورهای بیمار
- `GET /timeline/api/reminders/overdue_reminders/` - یادآورهای عقب‌افتاده
- `GET /timeline/api/reminders/upcoming_reminders/` - یادآورهای آتی
- `POST /timeline/api/reminders/{id}/mark_completed/` - علامت‌گذاری انجام شده
- `POST /timeline/api/reminders/create_from_template/` - ایجاد از قالب

### Template APIs
- `GET /timeline/api/reminder-templates/` - لیست قالب‌های یادآوری
- `GET /timeline/api/reminder-templates/by_test_type/?test_type=HBA1C` - قالب بر اساس نوع

## صفحات وب

### صفحه تایم‌لاین بیمار
- آدرس: `/timeline/patient/{patient_id}/timeline/`
- نمایش تعاملی تایم‌لاین با نمودار
- مدیریت یادآورها
- فیلترهای پیشرفته

## Management Commands

### ارسال یادآورها
```bash
# نمایش یادآورهای قابل ارسال
python manage.py send_test_reminders --dry-run

# ارسال واقعی یادآورها
python manage.py send_test_reminders
```

### ایجاد قالب‌های پیش‌فرض
```bash
python manage.py create_reminder_templates
```

### ایجاد داده‌های نمونه
```bash
# برای بیمار خاص
python manage.py create_sample_timeline --patient-id=1

# ایجاد بیمار و داده‌های نمونه
python manage.py create_sample_timeline
```

## Signals و یکپارچگی

سیستم به طور خودکار با سایر بخش‌های GitDM یکپارچه می‌شود:

- **هنگام ثبت مواجهه جدید**: رویداد تایم‌لاین ایجاد می‌شود
- **هنگام ثبت نتیجه آزمایش**: رویداد تایم‌لاین ایجاد شده و یادآوری مربوطه به‌روزرسانی می‌شود
- **هنگام سررسید یادآوری**: notification خودکار ارسال می‌شود

## مدل‌های داده

### MedicalTimeline
- ثبت تمام رویدادهای پزشکی در خط زمان
- ارتباط Generic با سایر مدل‌ها
- متادیتای JSON برای اطلاعات اضافی

### TestReminder  
- مدیریت یادآورهای دوره‌ای آزمایشات
- محاسبه خودکار تاریخ سررسید بعدی
- پشتیبانی از فرکانس‌های مختلف

### ReminderTemplate
- قالب‌های از پیش تعریف شده برای یادآورها
- شامل دستورالعمل‌ها و نکات آماده‌سازی

## امنیت و دسترسی

- کنترل دسترسی بر اساس رابطه پزشک-بیمار
- Audit logging تمام عملیات
- اعتبارسنجی داده‌های ورودی

## نمونه استفاده

```python
from timeline.services import TimelineService, ReminderService

# دریافت تایم‌لاین بیمار
timeline = TimelineService.get_patient_timeline(patient)

# ایجاد یادآورهای پیش‌فرض
reminders = ReminderService.create_default_reminders_for_patient(patient, doctor)

# بررسی یادآورهای عقب‌افتاده
overdue = ReminderService.get_overdue_reminders(doctor)
```