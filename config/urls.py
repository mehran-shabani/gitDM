from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularJSONAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    # Serve JSON explicitly to satisfy tests checking for 'json' in Content-Type
    path('api/schema/', SpectacularJSONAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    # JWT aliases (ensure availability even if api.urls not loaded)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
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
