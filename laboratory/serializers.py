from rest_framework import serializers
from .models import LabResult


class LabResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = LabResult
        fields = ['id', 'patient', 'encounter', 'loinc', 'value', 'unit', 'taken_at']
        read_only_fields = ['id']