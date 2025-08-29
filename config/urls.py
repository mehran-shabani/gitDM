from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
]

# Include api.routers if available
from importlib.util import find_spec
import logging
logger = logging.getLogger(__name__)
if find_spec('api.routers') is not None:
    try:
        urlpatterns.append(path('', include('api.routers')))
    except Exception as exc:  # فقط لاگ کن، قورت نده
        logger.warning("Skipping api.routers include due to error: %s", exc)
