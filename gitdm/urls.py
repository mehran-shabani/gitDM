"""
URL configuration for gitdm project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('patients/', include('patients_core.urls')),
    path('encounters/', include('diab_encounters.urls')),
    path('labs/', include('diab_labs.urls')),
    path('medications/', include('diab_medications.urls')),
    path('ai/', include('ai_summarizer.urls')),
    path('clinical-refs/', include('clinical_refs.urls')),
]