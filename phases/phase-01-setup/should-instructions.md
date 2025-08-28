# دستورالعمل اجرای فاز ۰۱

1) ساخت و فعال‌سازی ویرچوال‌انو:
   python -m venv .venv && source .venv/bin/activate
2) نصب وابستگی‌ها:
   pip install -r requirements.txt
3) ساخت فایل env بر اساس `.env` نمونه
4) راه‌اندازی Docker Compose:
   docker compose up -d db redis minio
5) انجام مایگریت و ساخت ادمین:
   python manage.py migrate && python manage.py createsuperuser
6) اجرای سرویس‌ها:
   docker compose up -d web worker beat
7) بررسی سلامت:
   curl http://localhost:8000/health/