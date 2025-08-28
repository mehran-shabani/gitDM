# دستورالعمل اجرای فاز ۰۳
1) افزودن AppConfig و signals به `records_versioning`
2) اجرای `python manage.py makemigrations records_versioning && python manage.py migrate`
3) تنظیم `SYSTEM_USER_ID` در settings در صورت نیاز
4) اجرای تست‌ها: `pytest -q`
5) بررسی API:
   - GET /api/versions/Patient/{patient_uuid}/
   - POST /api/versions/revert {resource_type, resource_id, target_version, user_id}