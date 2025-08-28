from rest_framework import serializers
from patients_core.models import Patient
from diab_encounters.models import Encounter
from diab_labs.models import LabResult
from diab_medications.models import MedicationOrder
from clinical_refs.models import ClinicalReference


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'national_id', 'full_name', 'dob', 'sex', 'primary_doctor_id', 'created_at']
        read_only_fields = ['id', 'created_at']


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
        fields = ['id', 'patient', 'encounter', 'atc', 'name', 'dose', 'frequency', 'route', 'start_date', 'end_date']
        read_only_fields = ['id']


class ClinicalReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClinicalReference
        fields = ['id', 'title', 'source', 'year', 'url', 'topic']
        read_only_fields = ['id']