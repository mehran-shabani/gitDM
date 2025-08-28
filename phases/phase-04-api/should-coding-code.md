# کدهای الزامی – API

## config/settings.py (بخش‌های افزوده/به‌روزشده)
REST_FRAMEWORK.update({
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
})

SYSTEM_USER_ID = '00000000-0000-0000-0000-000000000001'

## api/serializers.py (جدید)
from rest_framework import serializers
from patients_core.models import Patient
from diab_encounters.models import Encounter
from diab_labs.models import LabResult
from diab_medications.models import MedicationOrder
from clinical_refs.models import ClinicalReference

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id','national_id','full_name','dob','sex','primary_doctor_id','created_at']
        read_only_fields = ['id','created_at']

class EncounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Encounter
        fields = ['id','patient','occurred_at','subjective','objective','assessment','plan','created_by','created_at']
        read_only_fields = ['id','created_at','created_by']

class LabResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResult
        fields = ['id','patient','encounter','loinc','value','unit','taken_at']
        read_only_fields = ['id']

class MedicationOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationOrder
        fields = ['id','patient','encounter','atc','name','dose','frequency','route','start_date','end_date']
        read_only_fields = ['id']

class ClinicalReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalReference
        fields = ['id','title','source','year','url','topic']
        read_only_fields = ['id']

## api/views.py (جدید)
from uuid import UUID
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from patients_core.models import Patient
from diab_encounters.models import Encounter
from diab_labs.models import LabResult
from diab_medications.models import MedicationOrder
from clinical_refs.models import ClinicalReference
from ai_summarizer.models import AISummary
from .serializers import (
    PatientSerializer, EncounterSerializer, LabResultSerializer,
    MedicationOrderSerializer, ClinicalReferenceSerializer
)

SYSTEM_USER_ID = UUID(getattr(settings, 'SYSTEM_USER_ID'))

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('-created_at')
    serializer_class = PatientSerializer

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        p = self.get_object()
        enc = Encounter.objects.filter(patient=p).order_by('-occurred_at')
        labs = LabResult.objects.filter(patient=p).order_by('-taken_at')
        meds = MedicationOrder.objects.filter(patient=p).order_by('-start_date')
        summaries = AISummary.objects.filter(patient=p).order_by('-created_at')[:5]
        return Response({
            'patient': PatientSerializer(p).data,
            'encounters': EncounterSerializer(enc, many=True).data,
            'labs': LabResultSerializer(labs, many=True).data,
            'medications': MedicationOrderSerializer(meds, many=True).data,
            'ai_summaries': [
                {
                    'resource_type': s.resource_type,
                    'resource_id': str(s.resource_id),
                    'summary': s.summary,
                    'created_at': s.created_at,
                } for s in summaries
            ]
        })

class EncounterViewSet(viewsets.ModelViewSet):
    queryset = Encounter.objects.all().order_by('-occurred_at')
    serializer_class = EncounterSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=SYSTEM_USER_ID)

class LabResultViewSet(viewsets.ModelViewSet):
    queryset = LabResult.objects.all().order_by('-taken_at')
    serializer_class = LabResultSerializer

class MedicationOrderViewSet(viewsets.ModelViewSet):
    queryset = MedicationOrder.objects.all().order_by('-start_date')
    serializer_class = MedicationOrderSerializer

class ClinicalReferenceViewSet(viewsets.ModelViewSet):
    queryset = ClinicalReference.objects.all().order_by('-year')
    serializer_class = ClinicalReferenceSerializer

## api/urls.py (جدید)
from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    PatientViewSet, EncounterViewSet, LabResultViewSet,
    MedicationOrderViewSet, ClinicalReferenceViewSet
)

router = SimpleRouter()
router.register(r'patients', PatientViewSet, basename='patients')
router.register(r'encounters', EncounterViewSet, basename='encounters')
router.register(r'labs', LabResultViewSet, basename='labs')
router.register(r'meds', MedicationOrderViewSet, basename='meds')
router.register(r'refs', ClinicalReferenceViewSet, basename='refs')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

## config/urls.py (به‌روزرسانی)
from django.contrib import admin
from django.urls import path, include
from api import urls as api_urls
from api.routers import urlpatterns as health_urls  # اگر health در فاز 01 بوده

urlpatterns = [
    path('admin/', admin.site.urls),
]
urlpatterns += api_urls.urlpatterns
try:
    urlpatterns += health_urls
except Exception:
    pass

## api/routers.py (به‌روزرسانی در صورت نیاز)
from django.urls import path
from django.http import JsonResponse

def health(request):
    return JsonResponse({"status":"ok"})

urlpatterns = [path('health/', health)]