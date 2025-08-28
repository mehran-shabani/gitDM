from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from api.views import ClinicalReferenceViewSet

router = DefaultRouter()
router.register(r'refs', ClinicalReferenceViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('api.routers')),
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]