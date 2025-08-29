import json
import uuid
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_token_and_create_patient():
    """
    آزمونی که جریان احراز هویت مبتنی بر JWT و ایجاد/دریافت موجودیت بیمار را بررسی می‌کند.
    
    شرح جزئیات:
    - یک کاربر دیتابیس با نام‌کاربری 'u1' و رمز 'p1' ایجاد می‌کند (نیاز به دسترسی به پایگاه‌داده دارد).
    - با استفاده از APIClient یک درخواست POST به `/api/token/` ارسال می‌کند تا توکن‌های `access` و `refresh` را دریافت کند؛ وجود هر دو توکن و وضعیت HTTP 200 بررسی می‌شود.
    - توکن دسترسی (`access`) را در هدر Authorization به شکل `Bearer <token>` تنظیم می‌کند تا درخواست‌های محافظت‌شده را مجاز سازد.
    - یک بارگزاری (payload) برای ساخت بیمار شامل `full_name` و `primary_doctor_id` ارسال شده به `/api/patients/` فرستاده می‌شود؛ انتظار پاسخ HTTP 201 و برگردانده شدن شناسه بیمار وجود دارد.
    - با استفاده از شناسه برگردانده‌شده، یک درخواست GET به `/api/patients/{id}/timeline/` ارسال شده و انتظار وضعیت HTTP 200 برای بازیابی timeline بیمار وجود دارد.
    
    تأثیرات جانبی:
    - یک کاربر و یک رکورد بیمار در دیتابیس ایجاد می‌شوند.
    - از مسیرهای HTTP مشخص‌شده و مکانیزم JWT برای احراز هویت استفاده می‌شود.
    
    بدون مقدار بازگشتی؛ شکست در هر یک از assertها باعث شکست تست می‌شود.
    """
    User.objects.create_user(username='u1', password='p1')
    c = APIClient()
    r = c.post('/api/token/', {'username': 'u1', 'password': 'p1'}, format='json')
    assert r.status_code == 200
    assert 'access' in r.data and 'refresh' in r.data
    token = r.data['access']
    c.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    payload = {
        'full_name': 'Ali Test',
        'primary_doctor_id': '00000000-0000-0000-0000-000000000010'
    }
    r2 = c.post('/api/patients/', payload, format='json')
    assert r2.status_code == 201
    pid = r2.data['id']
    r3 = c.get(f'/api/patients/{pid}/timeline/')
    assert r3.status_code == 200
