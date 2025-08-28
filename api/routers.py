from django.urls import path
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_GET

@require_GET
def health(_request: HttpRequest) -> JsonResponse:
    """لایونس‌چک ساده: 200 و {"status": "ok"}؛ فقط GET/HEAD و کش غیرفعال."""
    return JsonResponse({"status": "ok"})

urlpatterns = [path('health/', health, name='health')]