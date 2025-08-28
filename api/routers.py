from django.urls import path
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_safe
from django.views.decorators.cache import never_cache

app_name = "api"

@never_cache
@require_safe
def health(_request: HttpRequest) -> JsonResponse:
    """لایونس‌چک ساده: 200 و {"status": "ok"}؛ فقط GET/HEAD و کش غیرفعال."""
    return JsonResponse({"status": "ok"})

urlpatterns = [path('health/', health, name='health')]