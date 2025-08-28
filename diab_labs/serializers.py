from rest_framework import serializers
from .models import Lab

class LabSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lab
        fields = ['id', 'patient', 'loinc', 'value', 'unit', 'taken_at', 'created_at', 'updated_at']