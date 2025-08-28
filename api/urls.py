from django.urls import path
from django.http import JsonResponse
from .views_export import export_patient

def health(request):
    return JsonResponse({"status":"ok"})

urlpatterns = [
    path('health/', health),
    path('export/patient/<uuid:pk>/', export_patient, name='export_patient'),
]