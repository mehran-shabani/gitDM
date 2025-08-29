from django.urls import path, include

# Root level API endpoints - now handled by gateway/urls.py
urlpatterns = [
    path('api/', include('gateway.urls')),
]