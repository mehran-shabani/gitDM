from rest_framework import serializers
from patients_core.models import Patient
from diab_encounters.models import Encounter
from diab_labs.models import LabResult
from diab_medications.models import MedicationOrder
from clinical_refs.models import ClinicalReference
from ai_summarizer.models import AISummary


class PatientSerializer(serializers.ModelSerializer):
    primary_doctor_id = serializers.IntegerField(source='primary_doctor.id', read_only=True)
    class Meta:
        model = Patient
        fields = ['id', 'national_id', 'full_name', 'dob', 'sex', 'primary_doctor', 'primary_doctor_id', 'created_at']
        read_only_fields = ['id', 'created_at', 'primary_doctor_id', 'primary_doctor']


class EncounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Encounter
        fields = ['id', 'patient', 'occurred_at', 'subjective', 'objective', 'assessment', 'plan', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_at', 'created_by']


class LabResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResult
        fields = ['id', 'patient', 'encounter', 'loinc', 'value', 'unit', 'taken_at']
        read_only_fields = ['id']


class MedicationOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationOrder
        fields = ['id', 'patient', 'encounter', 'atc', 'name', 'dose', 'frequency', 'start_date', 'end_date']
        read_only_fields = ['id']


class ClinicalReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalReference
        fields = ['id', 'title', 'source', 'year', 'url', 'topic']
        read_only_fields = ['id']


class AISummarySerializer(serializers.ModelSerializer):
    resource_type = serializers.CharField(read_only=True)
    resource_id = serializers.SerializerMethodField()
    
    class Meta:
        model = AISummary
        fields = ['id', 'resource_type', 'resource_id', 'summary', 'created_at']
        read_only_fields = ['id', 'resource_type', 'resource_id', 'created_at']
    
    def get_resource_id(self, obj):
        """
        یک‌خطی: شناسهٔ منبع مرتبط با AISummary را به صورت رشته برمی‌گرداند.
        
        توضیحات:
        این متد مقدار صفت `object_id` از نمونهٔ ورودی `obj` را گرفته و آن را به رشته تبدیل می‌کند تا برای فیلد سریالایزر `resource_id` قابل استفاده باشد. تبدیل به رشته تضمین می‌کند که مقدار بازگشتی مستقل از نوع اصلی (مثلاً UUID، عدد صحیح یا مقدار None) به شکل یک مقدار متنی عرضه شود.
        
        Parameters:
            obj: نمونهٔ مدل AISummary یا هر آبجکتی که صفت `object_id` را داشته باشد.
        
        Returns:
            str: مقدار `object_id` به صورت رشته.
        """
        return str(obj.object_id)
