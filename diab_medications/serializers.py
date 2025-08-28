from rest_framework import serializers
from .models import Medication

class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ['id', 'patient', 'atc', 'name', 'dose', 'frequency', 'start_date', 'end_date', 'created_at', 'updated_at']