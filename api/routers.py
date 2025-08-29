from django.urls import path, include
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_safe
from django.views.decorators.cache import never_cache
from rest_framework import routers
from api.versions import VersionViewSet

app_name = "api"

# Create DRF router
router = routers.DefaultRouter()

# Add version viewset - but don't register it as it has custom routes
# router.register(r'versions', VersionViewSet, basename='version')

@never_cache
@require_safe
def health(_request: HttpRequest) -> JsonResponse:
    """
    بررسی سلامت سادهٔ سرویس — پاسخ JSON {"status": "ok"} با وضعیت HTTP 200.
    
    این نما برای درخواست‌های ایمن (فقط GET/HEAD) در نظر گرفته شده و پاسخ آن نباید کش شود.
    پارامترها:
        _request (HttpRequest): جسم درخواست ارسالی؛ در این نما استفاده نمی‌شود و فقط برای انطباق با امضای نمای Django پذیرفته شده است.
    
    بازگشت:
        JsonResponse: پاسخ HTTP با بدنه‌ی JSON برابر {"status": "ok"} و کد وضعیت 200.
    """
    return JsonResponse({"status": "ok"})

# Create version views
version_list = VersionViewSet.as_view({'get': 'list'})
version_revert = VersionViewSet.as_view({'post': 'revert'})

urlpatterns = [
    path('health/', health, name='health'),
    path('', include(router.urls)),
    path('versions/<str:resource_type>/<uuid:resource_id>/', version_list, name='version-list'),
    path('versions/<str:resource_type>/<uuid:resource_id>/revert/', version_revert, name='version-revert'),
]