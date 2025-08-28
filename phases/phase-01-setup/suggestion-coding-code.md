# دستورات پیشنهادی کدنویسی (Setup)

## ۱) ایجاد پروژه و اپ‌ها
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install django djangorestframework psycopg2-binary python-dotenv djangorestframework-simplejwt celery redis minio django-storages boto3 drf-spectacular uvicorn

django-admin startproject config .
python manage.py startapp patients_core
python manage.py startapp diab_encounters
python manage.py startapp diab_labs
python manage.py startapp diab_medications
python manage.py startapp records_versioning
python manage.py startapp ai_summarizer
python manage.py startapp clinical_refs

## ۲) فایل‌های پایه
mkdir api services infra scripts

## ۳) مایگریت و ادمین
python manage.py migrate
python manage.py createsuperuser

## ۴) اجرای محلی (بدون Docker)
uvicorn config.asgi:application --host 0.0.0.0 --port 8000