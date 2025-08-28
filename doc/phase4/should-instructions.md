# دستورالعمل اجرای فاز ۰۴
1) نصب simplejwt در requirements (انجام شده)
2) `python manage.py makemigrations && python manage.py migrate`
3) ساخت User در ادمین یا تست: `createsuperuser`
4) دریافت توکن: POST /api/token/ {username,password}
5) ساخت Patient: POST /api/patients/
6) مشاهده تایم‌لاین: GET /api/patients/{id}/timeline/