from django.urls import path, include
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_safe
from django.views.decorators.cache import never_cache
from api.versions import VersionViewSet

app_name = "api"


@never_cache
@require_safe
def health(_request: HttpRequest) -> JsonResponse:
    """سلامت سرویس: JSON {"status": "ok"} با HTTP 200. بدون کش."""
    return JsonResponse({"status": "ok"})

# Create version views
version_list = VersionViewSet.as_view({'get': 'list'})
version_revert = VersionViewSet.as_view({'post': 'revert'})

urlpatterns = [
    path('health/', health, name='health'),
    path(
        'versions/<str:resource_type>/<int:resource_id>/',
        version_list,
        name='version-list',
    ),
    path(
        'versions/<str:resource_type>/<int:resource_id>/revert/',
        version_revert,
        name='version-revert',
    ),
 ]
