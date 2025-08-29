from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from api.versions import VersionViewSet

# Create the version_revert view
version_revert = VersionViewSet.as_view({'post': 'revert'})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('api.routers')),
    path('api/versions/revert/', version_revert),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]