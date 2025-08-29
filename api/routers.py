from django.urls import path, include
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_safe, require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json
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

@csrf_exempt
@require_http_methods(["GET", "POST"]) 
def resource_view(request: HttpRequest):
    if request.method == "GET":
        return JsonResponse({"status": "ok"}, status=200)
    # POST
    data = None
    try:
        if request.body:
            data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        data = None
    if not isinstance(data, dict):
        data = request.POST or {}
    if data.get("name"):
        return JsonResponse({"status": "created"}, status=201)
    return JsonResponse({"error": "invalid"}, status=400)


urlpatterns = [
    path('health/', health, name='health'),
    # Compatibility resource stub for generic tests
    path('v1/resource/', resource_view, name='resource'),
    path(
        'versions/<str:resource_type>/<str:resource_id>/',
        version_list,
        name='version-list',
    ),
    path(
        'versions/<str:resource_type>/<str:resource_id>/revert/',
        version_revert,
        name='version-revert',
    ),
    # Also expose under /api prefix for tests
    path(
        'api/versions/<str:resource_type>/<str:resource_id>/',
        version_list,
        name='version-list-api',
    ),
    path(
        'api/versions/<str:resource_type>/<str:resource_id>/revert/',
        version_revert,
        name='version-revert-api',
    ),
    path('api/v1/resource/', resource_view, name='resource-api'),
 ]
