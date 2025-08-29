# راهنمای احراز هویت و مدیریت کاربران

## نحوه کارکرد سیستم احراز هویت

### 1. ساخت کاربر - فقط از طریق Django Admin

**مهم**: در این پروژه هیچ API عمومی برای ثبت‌نام وجود ندارد. این یک تصمیم امنیتی است.

#### مراحل ساخت کاربر:

1. **ایجاد superuser اولیه** (در صورت نیاز):
```bash
python manage.py createsuperuser
```

2. **ورود به پنل ادمین**:
```
http://localhost:8000/admin/
```

3. **ساخت کاربر جدید**:
   - به بخش "Users" بروید
   - روی "Add User" کلیک کنید
   - username و password وارد کنید
   - ذخیره کرده و سطوح دسترسی را تنظیم کنید

### 2. دریافت JWT Token

کاربران باید با username/password خود token دریافت کنند:

```bash
POST /api/token/
Content-Type: application/json

{
    "username": "your_username",
    "password": "your_password"
}
```

پاسخ:
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 3. استفاده از Token در API

برای تمام درخواست‌های API، باید access token را در header ارسال کنید:

```bash
GET /api/patients/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 4. Refresh Token

Access token بعد از 60 دقیقه منقضی می‌شود. برای دریافت token جدید:

```bash
POST /api/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## User Model

این پروژه از `get_user_model()` Django استفاده می‌کند که به طور پیش‌فرض User استاندارد Django با integer primary key است.

## نکات امنیتی

- عدم وجود API ثبت‌نام عمومی باعث کنترل کامل روی دسترسی‌ها می‌شود
- همه کاربران توسط ادمین مدیریت می‌شوند
- JWT tokens stateless هستند و نیازی به session ندارند
- تمام endpoint‌های API نیاز به authentication دارند (به جز /api/token/)

## System User

یک کاربر سیستمی با ID مشخص (`SYSTEM_USER_ID`) برای عملیات خودکار استفاده می‌شود. این کاربر باید در دیتابیس ایجاد شود.