from django.urls import path
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_GET

@require_GET
def health(_request: HttpRequest) -> JsonResponse:
    """
    بررسی سلامت سادهٔ سرویس و بازگشت وضعیت به‌صورت JSON.
    
    این ویو برای endpoint سلامت (health check) پاسخ می‌دهد و یک پاسخ JSON شامل {"status": "ok"} با کد وضعیت HTTP 200 برمی‌گرداند.
    پارامتر _request از نوع HttpRequest دریافت می‌شود اما در منطق تابع استفاده نمی‌شود (وجود آن برای سازگاری با امضای ویوهای Django لازم است).
    """
    return JsonResponse({"status": "ok"})

urlpatterns = [path('health/', health, name='health')]